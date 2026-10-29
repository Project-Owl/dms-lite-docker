"""Bounded, secret-safe Docker process boundary for an explicit migration."""
import csv
import io
import json
import os
import subprocess
import uuid
from pathlib import Path
from .paths import MigrationError

LEGACY_IMAGE='linuxserver/mariadb:10.5.13-r0-ls43@sha256:f2d75029f8f1788201ca2c2f6e7d0967b893875530e1d9007da6323351c3726c'
TARGET_IMAGE='mariadb:11.4.13@sha256:250e1609e93c0e6aecf64bfbab2d84d5e89d2481540fe77447ff6c855c3b1873'
LABEL='io.projectowl.dms-migration'

def mount_spec(source,target,readonly=False):
    output=io.StringIO();csv.writer(output).writerow(['type=bind','source='+str(source),'target='+target,*(['readonly'] if readonly else [])])
    return output.getvalue().strip('\r\n')

class DockerRunner:
    def __init__(self,timeout=600,execute=subprocess.run):
        self.timeout=timeout;self.execute=execute;self.run_id=uuid.uuid4().hex
        self.prefix='dms-migrate-'+self.run_id[:16];self.containers=set()

    def run(self,args,*,env=None,input=None,stdin=None,stdout=None,phase='Docker operation'):
        try:
            result=self.execute(['docker',*args],env={**os.environ,**(env or {})},input=input,stdin=stdin,
                stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,timeout=self.timeout)
        except (OSError,subprocess.TimeoutExpired):
            raise MigrationError(phase+' failed or timed out') from None
        if result.returncode:
            raise MigrationError(phase+' failed (exit '+str(result.returncode)+'); original data is unchanged')
        return result.stdout or b''

    def assert_local(self):
        if os.getenv('DOCKER_HOST') and not os.environ['DOCKER_HOST'].startswith('unix://'):
            raise MigrationError('Migration requires a local Unix-socket Docker daemon')
        endpoint=json.loads(self.run(['context','inspect','--format','{{json .Endpoints.docker.Host}}'],phase='Docker context check'))
        if not endpoint.startswith('unix://'):
            raise MigrationError('Migration requires a local Unix-socket Docker daemon')

    def running_mounts(self):
        result=[]
        for container in self.run(['ps','-q'],phase='Running-container inspection').decode().split():
            owner=self.run(['inspect','--format','{{index .Config.Labels "'+LABEL+'"}}',container],phase='Mount ownership check').decode().strip()
            if owner==self.run_id: continue
            mounts=json.loads(self.run(['inspect','--format','{{json .Mounts}}',container],phase='Mount inspection'))
            result.extend(mount['Source'] for mount in mounts if mount.get('Source'))
        return result

    def owned_args(self,role):
        name=self.prefix+'-'+role;self.containers.add(name)
        return name,['--name',name,'--label',LABEL+'='+self.run_id,'--network','none']

    def copy_source(self,source,workspace):
        _,owned=self.owned_args('copy')
        self.run(['run',*owned,'--user','0','--entrypoint','sh','--mount',mount_spec(source,'/source',True),
            '--mount',mount_spec(workspace,'/backup'),LEGACY_IMAGE,'-c','cp -a /source/. /backup/legacy-data'],phase='Cold source copy')
        return workspace/'legacy-data'

    def start_source(self,copy):
        name,owned=self.owned_args('source')
        self.run(['run','-d',*owned,'--user','0','--entrypoint','mysqld','--mount',mount_spec(copy,'/config'),LEGACY_IMAGE,
            '--no-defaults','--user=root','--datadir=/config/databases','--socket=/tmp/migration.sock','--pid-file=/tmp/migration.pid',
            '--bind-address=127.0.0.1','--port=3306','--skip-name-resolve'],phase='Legacy copied-server start')
        return name

    def start_target(self,destination,credentials):
        name,owned=self.owned_args('target')
        env={'MARIADB_ROOT_PASSWORD':credentials.root_password,'MARIADB_DATABASE':credentials.database,
             'MARIADB_USER':credentials.user,'MARIADB_PASSWORD':credentials.password}
        self.run(['run','-d',*owned,*[part for key in env for part in ('--env',key)],
                  '--mount',mount_spec(destination,'/var/lib/mysql'),TARGET_IMAGE],env=env,phase='Fresh target start')
        return name

    def stop_clean(self,name):
        self.run(['stop','--time','30',name],phase='Verified server shutdown')
        code=self.run(['inspect','--format','{{.State.ExitCode}}',name],phase='Shutdown status check').decode().strip()
        if code!='0': raise MigrationError('Server did not shut down cleanly; destination retained for inspection')

    def cleanup(self):
        if not self.containers: return
        names=', '.join(sorted(self.containers))
        try:
            existing=self.run(['ps','--all','--filter','label='+LABEL+'='+self.run_id,'--format','{{.Names}}'],phase='Cleanup resource inspection').decode().splitlines()
            for name in existing:
                if name not in self.containers: continue
                owner=self.run(['inspect','--format','{{index .Config.Labels "'+LABEL+'"}}',name],phase='Cleanup ownership check').decode().strip()
                if owner!=self.run_id: raise MigrationError('Temporary resource ownership changed')
                self.run(['rm','--force',name],phase='Temporary-container cleanup')
        except MigrationError:
            raise MigrationError('Temporary-container cleanup could not be confirmed; inspect owned resources: '+names) from None
