"""Opt-in Docker device permission integration: DMS_IMAGE_TESTS=1."""
import os
import pathlib
import pty
import select
import subprocess
import unittest

@unittest.skipUnless(os.getenv('DMS_IMAGE_TESTS')=='1','set DMS_IMAGE_TESTS=1 to run Docker device integration')
class ContainerSerialTests(unittest.TestCase):
    def test_nonroot_serial_access_requires_the_explicit_device_group(self):
        master,slave=pty.openpty()
        device=os.ttyname(slave)
        os.fchown(slave,-1,os.getgid());os.fchmod(slave,0o660)
        command=['docker','run','--rm','--device',device+':/dev/ttyUSB0','--mount','type=bind,src='+device+',dst=/dev/ttyUSB0','--entrypoint','python','dms-lite-smoke-serialwriter']
        try:
            denied=subprocess.run(command+['-c',"import serial; serial.Serial('/dev/ttyUSB0')"],capture_output=True,text=True,timeout=20)
            self.assertNotEqual(denied.returncode,0)
            self.assertIn('Permission denied',denied.stderr)
            allowed=command[:3]+['--group-add',str(os.getgid())]+command[3:]
            probe="import os,serial; assert os.getuid()==10001; p=serial.Serial('/dev/ttyUSB0',115200,timeout=5); print('READY',flush=True); assert p.readline()==b'packet\\n'; p.write(b'ack\\n'); p.close(); print('PASS',flush=True)"
            process=subprocess.Popen(allowed+['-c',probe],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                ready,_,_=select.select([process.stdout],[],[],15)
                self.assertTrue(ready)
                line=process.stdout.readline().strip()
                if line!='READY':
                    out,err=process.communicate(timeout=5)
                    self.fail('Container serial open failed: '+err)
                os.write(master,b'packet\n')
                readable,_,_=select.select([master],[],[],10)
                self.assertTrue(readable)
                self.assertEqual(os.read(master,100),b'ack\n')
                out,err=process.communicate(timeout=10)
                self.assertEqual(process.returncode,0,err)
                self.assertIn('PASS',out)
            finally:
                if process.poll() is None: process.terminate();process.communicate(timeout=10)
                process.stdout.close();process.stderr.close()
        finally: os.close(master);os.close(slave)

if __name__=='__main__': unittest.main()
