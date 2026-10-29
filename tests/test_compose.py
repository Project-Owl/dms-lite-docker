import json
import os
import pathlib
import subprocess
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
ENV=dict(os.environ,MYSQL_DATABASE='test',MYSQL_USER='test',MYSQL_PASSWORD='test-password',MYSQL_ROOT_PASSWORD='test-root',MYSQL_HOST='mariadb',DATABASE_DATA_DIR=str(ROOT/'data-mariadb'))
def config(*files):
    result=subprocess.run(['docker','compose','--env-file','/dev/null',*[arg for f in files for arg in ('-f',str(ROOT/f))],'config','--format','json'],env=ENV,capture_output=True,text=True,check=True)
    return json.loads(result.stdout)
class ComposeTests(unittest.TestCase):
    def test_official_datadir_and_preserved_settings(self):
        services=config('docker-compose-base.yml','docker-compose-wifi.yml')['services']
        db=services['mariadb']
        self.assertEqual(db['volumes'][0]['target'],'/var/lib/mysql')
        self.assertEqual(db['volumes'][0]['source'],str(ROOT/'data-mariadb'))
        self.assertEqual(db['environment']['MARIADB_DATABASE'],'test')
        self.assertNotIn('PUID',db['environment'])
        self.assertFalse(db.get('ports'))
        self.assertEqual(services['web']['environment']['MYSQL_DATABASE'],'test')
    def test_test_data_and_serial_device_permissions_are_isolated(self):
        cfg=config('docker-compose-base.yml','docker-compose-wifi.yml','tests/compose.smoke.yml')['services']
        self.assertEqual(cfg['mariadb']['volumes'][0]['type'],'volume')
        self.assertEqual(cfg['mariadb']['volumes'][0]['target'],'/var/lib/mysql')
        serial=config('docker-compose-base.yml','docker-compose-serial.yml')['services']
        self.assertTrue(serial['serialwriter']['group_add'])
        self.assertFalse(serial['serialwriter'].get('privileged'))
class SmokeIsolationTests(unittest.TestCase):
    def test_operator_mqtt_configuration_is_ignored(self):
        import importlib.util
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('stack_smoke',ROOT/'tests/smoke.py');module=importlib.util.module_from_spec(spec)
        with patch.dict(os.environ,{'MQTT_HOST':'operator-broker.example','MQTT_PORT':'21883','MQTT_TOPIC':'operator/#'}):
            spec.loader.exec_module(module)
        self.assertEqual(module.ENV['MQTT_HOST'],'mosquitto')
        self.assertEqual(module.ENV['MQTT_PORT'],'1883')
        self.assertIn('--env-file',module.COMPOSE)
        self.assertIn('/dev/null',module.COMPOSE)

if __name__=='__main__': unittest.main()
