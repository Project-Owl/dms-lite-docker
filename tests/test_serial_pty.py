import json
import os
import pathlib
import threading
import time
import unittest
from test_ingestion import adapters, PACKET, Connection
try:
    import serial
except ImportError:
    serial = None

@unittest.skipIf(serial is None, 'Install pyserial==3.5 to run the real pseudo-terminal test')
class SerialPtyTests(unittest.TestCase):
    def test_serial_transport_reads_real_split_frames_and_recovers_after_bad_packets(self):
        import pty
        master, slave = pty.openpty()
        device = os.ttyname(slave)
        stop, opened, stored = threading.Event(), threading.Event(), threading.Event()
        received=[]
        class Database(Connection):
            def cursor(self):
                cursor=super().cursor()
                original=cursor.execute
                def execute(sql,values=()):
                    original(sql,values)
                    if sql.startswith('INSERT'): received.append(values); stored.set()
                cursor.execute=execute
                return cursor
        def factory(*args,**kwargs):
            port=serial.Serial(*args,**kwargs);opened.set();return port
        worker=threading.Thread(target=adapters()[0].run_serial,args=(factory,Database,stop),kwargs={'device':device,'max_bytes':256},daemon=True)
        worker.start()
        try:
            self.assertTrue(opened.wait(3))
            os.write(master,b'bad-json\n'+b'x'*300+b'\n')
            raw=json.dumps(PACKET).encode()
            os.write(master,raw[:20]);time.sleep(1.2);os.write(master,raw[20:]+b'\n')
            self.assertTrue(stored.wait(4))
            self.assertEqual(tuple(received[0][1:]),('DUCK001','sensor/temp','MSG001','-2.5','A,B',2,1))
        finally:
            stop.set();worker.join(4);os.close(master);os.close(slave)
        self.assertFalse(worker.is_alive())

if __name__=='__main__': unittest.main()
