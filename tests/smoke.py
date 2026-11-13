"""Isolated Docker integration test. Requires Docker Compose 2.24.4 or newer."""
import json
import os
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROJECT = 'dms-lite-smoke-' + str(os.getpid())
ENV = dict(os.environ, MYSQL_HOST='mariadb', MYSQL_DATABASE='smoke', MYSQL_USER='smoke', MYSQL_PASSWORD='smoke_test_password', MYSQL_ROOT_PASSWORD='smoke_test_root', MQTT_HOST='mosquitto', MQTT_PORT='1883', MQTT_TOPIC='#', MAX_PACKET_BYTES='65536', DEVICE_STALE_SECONDS='300', WEB_PORT='3000', WEB_BIND_ADDRESS='127.0.0.1', MQTT_HOST_PORT='1883', MQTT_BIND_ADDRESS='127.0.0.1')
COMPOSE = ['docker','compose','--env-file','/dev/null','--project-name',PROJECT,'-f',str(ROOT/'docker-compose-base.yml'),'-f',str(ROOT/'docker-compose-wifi.yml'),'-f',str(ROOT/'tests/compose.smoke.yml')]

def compose(*args, stdin=None):
    result = subprocess.run(COMPOSE+list(args),cwd=ROOT,env=ENV,input=stdin,text=True,capture_output=True)
    if result.returncode:
        print(result.stdout[-6000:], flush=True)
        print(result.stderr[-6000:], flush=True)
        result.check_returncode()
    return result.stdout

def wait_for(check, seconds=120):
    end = time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            value=check()
            if value: return value
        except (subprocess.CalledProcessError, urllib.error.URLError, OSError, ValueError): pass
        time.sleep(1)
    raise AssertionError('Timed out waiting for test service or data')

def sql(statement):
    return compose('exec','-T','mariadb','sh','-c','export MYSQL_PWD="$MARIADB_PASSWORD"; exec mariadb --protocol=TCP -h 127.0.0.1 -u"$MARIADB_USER" "$MARIADB_DATABASE"',stdin=statement)

def validate_config():
    config=json.loads(compose('config','--format','json'))
    services=config['services']
    assert services['wifiwriter']['environment']['MQTT_HOST']=='mosquitto'
    assert str(services['wifiwriter']['environment']['MQTT_PORT'])=='1883'
    assert services['wifiwriter']['environment']['MQTT_TOPIC']=='#'
    assert services['web'].get('healthcheck'), 'web readiness healthcheck missing'
    assert services['wifiwriter']['depends_on']['web']['condition']=='service_healthy', 'writer must wait for schema owner'
    assert 'backend' not in services, 'Flask should not be deployed'
    assert services['mariadb']['volumes'][0]['type']=='volume', 'operator storage must not be mounted'
    assert all(volume['type']!='bind' for volume in services['mariadb']['volumes'])
    assert 'container_name' not in services['MQTT-Server'], 'test broker must not collide with operator containers'
    return config

def main():
    validate_config()
    print('Validated isolated configuration: '+PROJECT,flush=True)
    started=False
    try:
        started=True
        compose('up','-d','mariadb','MQTT-Server')
        wait_for(lambda: sql('SELECT 1;'))
        sql('CREATE TABLE clusterData (timestamp DATETIME, duck_id TEXT, topic TEXT, message_id TEXT, payload TEXT, path TEXT, hops INT, duck_type INT); CREATE TABLE clusterCommands (timestamp TEXT, topic TEXT, payload TEXT); INSERT INTO clusterData VALUES (\'2026-10-23 12:00:00\',\'EXISTING\',\'sensor/temp\',\'OLD\',\'1.25\',\'A\',0,1);')
        compose('up','-d','--build','web','wifiwriter')
        address=compose('port','web','3000').strip()
        url='http://'+address
        def get(path):
            with urllib.request.urlopen(url+path,timeout=20) as response: return json.load(response)
        wait_for(lambda: get('/health/ready'))
        assert get('/api/ducks')==['EXISTING'], 'startup must preserve seeded data'
        with urllib.request.urlopen(url+'/',timeout=20) as response: overview=response.read().decode()
        assert '<h1>Overview</h1>' in overview and 'EXISTING' in overview, 'real overview did not render seeded data'
        stylesheet=re.search(r'href="(/stylesheets/app\.css\?v=[a-f0-9]+)"',overview)
        assert stylesheet, 'versioned production stylesheet missing'
        with urllib.request.urlopen(url+stylesheet.group(1),timeout=20) as response: css=response.read().decode()
        assert '--surface-2:' in css and '--chart-series-1:' in css and '--color-accent' in css, 'compiled DMS Lite Tokens are missing'
        print('Real overview and versioned local styles passed',flush=True)
        # Established native connector operation must time out, not hang forever.
        compose('exec','-T','wifiwriter','python','-c',"""
import mariadb, time
from wifi_sqlwriter import connect_database
conn=connect_database(mariadb)
start=time.monotonic()
timed_out=False
try:
    conn.cursor().execute('SELECT SLEEP(8)')
except mariadb.Error:
    timed_out=True
finally:
    conn.close()
assert timed_out, 'established DB read did not time out'
assert time.monotonic()-start < 7, 'DB read deadline was not bounded'
""")
        def publish(payload):
            compose('exec','-T','MQTT-Server','mosquitto_pub','-h','127.0.0.1','-t','sensor/test','-m',payload)
        packet=json.loads((ROOT/'tests/fixtures/packets.json').read_text())
        def ingest(message_id):
            packet['MessageID']=message_id
            publish('{')
            publish(json.dumps(packet))
            wait_for(lambda:any(row['message_id']==message_id for row in get('/data/getAllData')))
        ingest('SMOKE1')
        print('Seeded startup and MQTT ingestion passed',flush=True)
        assert get('/api/readings?topic=sensor%2Ftemp&limit=2')['samples'][-1]['value']==-2.5
        assert get('/api/alerts?topic=sensor%2Ftemp&min=0&max=10')['reading']['duckId']=='DUCK001'
        print('Checking database outage/recovery',flush=True)
        compose('stop','mariadb')
        try: get('/health/ready'); raise AssertionError('database outage reported ready')
        except urllib.error.HTTPError as error: assert error.code==503
        compose('start','mariadb');wait_for(lambda:get('/health/ready'))
        compose('restart','MQTT-Server');time.sleep(6)
        ingest('SMOKE2')
        assert 'EXISTING' in get('/api/ducks')
        # Empty-database behavior, inside this test-only volume.
        sql('DELETE FROM clusterData;')
        assert get('/api/topics')==[]
        assert get('/api/readings?topic=x')['samples']==[]
        ingest('SMOKE3')
        # A second cold start verifies that the web owner creates absent tables.
        compose('down','--volumes','--remove-orphans')
        compose('up','-d','web','wifiwriter','MQTT-Server')
        url='http://'+compose('port','web','3000').strip()
        wait_for(lambda:get('/health/ready'))
        assert get('/api/ducks')==[]
        ingest('FRESH')
        print('PASS: seeded/fresh startup, MQTT recovery, analytics and data preservation')
    finally:
        if started: compose('down','--volumes','--remove-orphans')

if __name__=='__main__': main()
