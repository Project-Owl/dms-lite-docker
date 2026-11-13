import importlib.util
import json
import pathlib
import threading
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKET = json.loads((ROOT / 'tests/fixtures/packets.json').read_text())
def load(name, folder, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / folder / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def adapters():
    return [load('serial_writer', 'serial-sql-writer', 'serial_sqlwriter.py'), load('wifi_writer', 'wifi-sql-writer', 'wifi_sqlwriter.py')]

class Cursor:
    def __init__(self, fail=False): self.fail, self.closed, self.inserts = fail, False, []
    def execute(self, sql, values=()):
        if self.fail: raise OSError('database unavailable')
        self.inserts.append((sql, values))
    def close(self): self.closed = True
class Connection:
    def __init__(self, fail=False): self.c = Cursor(fail); self.closed = self.committed = False
    def cursor(self): return self.c
    def commit(self): self.committed = True
    def rollback(self): pass
    def close(self): self.closed = True

class IngestionTests(unittest.TestCase):
    def test_both_adapters_validate_packets_and_preserve_text(self):
        for module in adapters():
            for payload in ['-2.5', 'text', '']:
                packet = dict(PACKET, Payload=payload, extra='allowed')
                self.assertEqual(module.decode_packet(json.dumps(packet).encode())['Payload'], payload)
            invalid = [b'\xff', b'{', b'[]', b'null', b'x'*65537]
            for key in PACKET:
                packet = dict(PACKET); del packet[key]; invalid.append(json.dumps(packet).encode())
            for key, value in [('hops', True),('hops',-1),('hops',1.5),('duckType',2147483648),('path',[]),('DeviceID','')]:
                invalid.append(json.dumps(dict(PACKET, **{key:value})).encode())
            for raw in invalid:
                with self.assertRaises(ValueError): module.decode_packet(raw)

    def test_storage_retries_closes_resources_and_records_utc_values(self):
        for module in adapters():
            conns = [Connection(True),Connection(True),Connection()]
            pending = iter(conns)
            self.assertTrue(module.store_packet(PACKET,lambda:next(pending),datetime(2026,10,23,12,tzinfo=timezone.utc),sleep=lambda _:None))
            self.assertTrue(all(c.closed and c.c.closed for c in conns))
            sql, values = conns[-1].c.inserts[0]
            self.assertIn('(timestamp, duck_id, topic, message_id, payload, path, hops, duck_type)',sql)
            self.assertEqual(tuple(values),('2026-10-23 12:00:00','DUCK001','sensor/temp','MSG001','-2.5','A,B',2,1))
            attempts=[]
            def failing(): attempts.append(1); raise OSError('offline')
            self.assertFalse(module.store_packet(PACKET,failing,datetime.now(timezone.utc),sleep=lambda _:None))
            self.assertEqual(len(attempts),3)

    def test_mysql_host_is_used_by_the_real_connection_boundary(self):
        for module in adapters():
            received={}
            def connect(**kwargs): received.update(kwargs); return Connection()
            module.connect_database(SimpleNamespace(connect=connect),{'MYSQL_USER':'u','MYSQL_PASSWORD':'p','MYSQL_HOST':'database','MYSQL_DATABASE':'d'})
            self.assertEqual(received['host'],'database')
            self.assertEqual(received['read_timeout'],5)
            self.assertEqual(received['write_timeout'],5)

    def test_mqtt_skips_bad_packets_and_recovers_after_store_exception(self):
        module=adapters()[1]; stored=[]
        def store(packet):
            stored.append(packet)
            if len(stored)==1: raise OSError('offline')
        on_connect,on_message=module.make_callbacks(store,'sensor/#',65536)
        subscribed=[]; on_connect(SimpleNamespace(subscribe=subscribed.append),None,None,0,None)
        self.assertEqual(subscribed,['sensor/#'])
        on_message(None,None,SimpleNamespace(payload=b'{'))
        for _ in range(2): on_message(None,None,SimpleNamespace(payload=json.dumps(PACKET).encode()))
        self.assertEqual(len(stored),2)

    def test_serial_preserves_split_frames_and_discards_oversized_frames(self):
        module=adapters()[0]; stop=threading.Event()
        chunks=iter([b'hel',b'',b'lo\n'+b'x'*40,b'bad-tail\nnext\n'])
        class Port:
            def read_until(self,*args):
                try: return next(chunks)
                except StopIteration: stop.set(); return b''
        self.assertEqual(list(module.read_frames(Port(),stop,32)),[b'hello',b'next'])

    def test_schema_wait_closes_connections_and_recovers(self):
        for module in adapters():
            conns=[Connection(True),Connection()]; pending=iter(conns)
            self.assertTrue(module.wait_for_schema(lambda:next(pending),threading.Event(),sleep=lambda _:None))
            self.assertTrue(all(c.closed and c.c.closed for c in conns))

if __name__ == '__main__': unittest.main()
