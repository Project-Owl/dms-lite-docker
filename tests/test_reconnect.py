import threading
import time
import unittest
from types import SimpleNamespace
from test_ingestion import adapters, Connection

class ReconnectTests(unittest.TestCase):
    def test_retired_dispatcher_cannot_follow_a_reconnected_port(self):
        module=adapters()[0]
        # Simulate a call exceeding the retirement join without an eight-second wait.
        class FastJoinThread(threading.Thread):
            def join(self,timeout=None): return super().join(min(timeout or 0.02,0.02))
        module.threading=SimpleNamespace(Thread=FastJoinThread,Event=threading.Event)
        stop=threading.Event();first_entered=threading.Event();second_opened=threading.Event();release_first=threading.Event()
        observed=[];ports=[]
        class Port:
            def __init__(self,index): self.index=index
            def read_until(self,*args):
                if self.index==1:
                    first_entered.wait(2)
                    raise OSError('disconnect')
                time.sleep(0.01);return b''
            def close(self): pass
        def factory(*args,**kwargs):
            port=Port(len(ports)+1);ports.append(port)
            if port.index==2: second_opened.set()
            return port
        def dispatch(connect,port):
            if port.index==1:
                first_entered.set();release_first.wait(5)
            observed.append((threading.get_ident(),port.index))
        runner=threading.Thread(target=module.run_serial,args=(factory,Connection,stop),kwargs={'dispatch':dispatch},daemon=True)
        runner.start()
        try:
            self.assertTrue(second_opened.wait(3))
            release_first.set();time.sleep(1.3)
            self.assertEqual(len({identity for identity,index in observed if index==2}),1)
        finally:
            release_first.set();stop.set();runner.join(3)
        self.assertFalse(runner.is_alive())

if __name__=='__main__': unittest.main()
