"""Runtime probes for locally built application images; no data mounts."""
import subprocess

def main():
    subprocess.run(['docker','run','--rm','--entrypoint','node','dms-lite-smoke-web','-e',"const assert=require('assert');assert.ok(process.getuid() !== 0);assert.ok(process.versions.node.startsWith('24.'));assert.ok(require('fs').readFileSync('/app/public/stylesheets/app.css','utf8').includes('--chart-series-1:'));assert.throws(()=>require.resolve('@tailwindcss/cli'));assert.throws(()=>require.resolve('tailwindcss'));"],check=True)
    probe="import os,sys,shutil,pathlib,mariadb; assert sys.version_info[:2]==(3,14); assert os.getuid()==10001; assert mariadb.__version__=='1.1.14'; assert shutil.which('gcc') is None; assert not pathlib.Path('/usr/include/mariadb').exists()"
    for kind in ('wifiwriter','serialwriter'):
        subprocess.run(['docker','run','--rm','--entrypoint','python','dms-lite-smoke-'+kind,'-c',probe],check=True)
    print('PASS: supported runtimes, native connector, non-root users and compiler-free images')

if __name__=='__main__': main()
