"""Real copy-only legacy migration rehearsal; all paths are generated under the configured temporary directory."""
import hashlib
import json
import os
import signal
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.migration.docker import DockerRunner,LEGACY_IMAGE,LABEL,mount_spec
from scripts.migration.verify import Credentials,DatabaseClient,identifier,literal

PYTHON_IMAGE='dms-lite-smoke-wifiwriter'

def tree_hash(runner,source):
    _,owned=runner.owned_args('hash')
    code="""import pathlib,hashlib,os
h=hashlib.sha256()
for p in sorted(pathlib.Path('/source').rglob('*')):
 s=p.lstat();h.update(str(p.relative_to('/source')).encode());h.update(str((s.st_mode,s.st_uid,s.st_gid)).encode())
 if p.is_symlink(): h.update(os.readlink(p).encode())
 elif p.is_file():
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
print(h.hexdigest())
"""
    return runner.run(['run','--rm',*owned,'--user','0','--entrypoint','python','--mount',mount_spec(source,'/source',True),PYTHON_IMAGE,'-c',code]).decode().strip()

def invoke(source,destination,backup,env_file,*,expect=0,extra_env=None):
    result=subprocess.run([sys.executable,str(ROOT/'scripts/migrate_database.py'),'--source',str(source),
        '--destination',str(destination),'--backup-root',str(backup),'--env-file',str(env_file),'--timeout-seconds','60'],capture_output=True,text=True,timeout=180,env={**os.environ,**(extra_env or {})})
    if result.returncode!=expect:
        import difflib
        for workspace in backup.glob('migration-*'):
            left=workspace/'source-schema.json';right=workspace/'target-schema.json'
            if left.exists() and right.exists():
                print(''.join(difflib.unified_diff(left.read_text().splitlines(True),right.read_text().splitlines(True))),flush=True)
        raise AssertionError('Helper result '+str(result.returncode)+': '+result.stderr+result.stdout)
    return result

def main():
    root=Path(tempfile.mkdtemp(prefix='dms-migration-test-'))
    source=root/'original';source.mkdir();destination=root/'destination';backups=root/'backups'
    runner=DockerRunner(timeout=90)
    simple=Credentials('smoke','smoke','initial-test-app','initial-test-root')
    creds=Credentials('smoke','smoke',"app # quote' $(never)",'root # quote" $(never)')
    envfile=root/'test.env'
    envfile.write_text('\n'.join(key+'='+json.dumps(value) for key,value in {
        'MYSQL_DATABASE':creds.database,'MYSQL_USER':creds.user,'MYSQL_PASSWORD':creds.password,'MYSQL_ROOT_PASSWORD':creds.root_password,'MYSQL_HOST':'mariadb'}.items())+'\n');envfile.chmod(0o600)
    fixture,owned=runner.owned_args('fixture')
    try:
        env={'MYSQL_DATABASE':simple.database,'MYSQL_USER':simple.user,'MYSQL_PASSWORD':simple.password,'MYSQL_ROOT_PASSWORD':simple.root_password,'PUID':str(os.getuid()),'PGID':str(os.getgid())}
        runner.run(['run','-d',*owned,*[a for key in env for a in ('--env',key)],'--mount',mount_spec(source,'/config'),LEGACY_IMAGE],env=env,phase='Legacy fixture initialization')
        deadline=time.monotonic()+90
        while b'[services.d] done.' not in runner.run(['logs',fixture]):
            if time.monotonic()>deadline: raise AssertionError('Legacy fixture initialization did not finish')
            time.sleep(0.5)
        old=DatabaseClient(runner,fixture,simple,legacy=True);old.ready()
        old.query("CREATE TABLE smoke.clusterData (timestamp DATETIME,duck_id TEXT,topic TEXT,message_id TEXT,payload TEXT,path TEXT,hops INT,duck_type INT) CHARACTER SET utf8mb4; CREATE TABLE smoke.clusterCommands(timestamp TEXT,topic TEXT,payload TEXT) CHARACTER SET utf8mb4; INSERT INTO smoke.clusterData VALUES ('2024-03-10 01:59:59','D1','sensor/temp','M1',CONVERT(UNHEX('"+'café 漢字'.encode().hex()+"') USING utf8mb4),'A,B',2,1),('2024-11-03 01:30:00','D2','sensor/temp','M2','',NULL,0,0),(NULL,'D3','text','M3',NULL,'',NULL,NULL); INSERT INTO smoke.clusterCommands VALUES ('same',' /wifi/','1D1'),('same',' /wifi/','1D1');")
        roots=old.json_rows("SELECT JSON_OBJECT('host',Host) FROM mysql.user WHERE User='root';")
        statements=['SET PASSWORD FOR `smoke`@`%` = PASSWORD('+literal(creds.password)+');']
        statements+=['SET PASSWORD FOR `root`@'+identifier(row['host'])+' = PASSWORD('+literal(creds.root_password)+');' for row in roots]
        old.query(''.join(statements))
        DatabaseClient(runner,fixture,creds,legacy=True).ready()
        from scripts.migrate_database import load_credentials
        loaded=load_credentials(runner,envfile)
        assert loaded==creds, 'Compose credential fields changed: '+','.join(name+':'+str(len(getattr(loaded,name)))+'/'+str(len(getattr(creds,name))) for name in ('database','user','password','root_password') if getattr(loaded,name)!=getattr(creds,name))
        runner.stop_clean(fixture)
        before=tree_hash(runner,source)
        print('Legacy fixture stopped; testing refusal paths',flush=True)
        occupied=root/'occupied';occupied.mkdir();(occupied/'keep').write_text('keep')
        invoke(source,occupied,root/'not-created',envfile,expect=1)
        assert (occupied/'keep').read_text()=='keep' and not (root/'not-created').exists()
        wrong=root/'wrong.env';wrong.write_text(envfile.read_text().replace(json.dumps(creds.root_password),json.dumps('incorrect-root')))
        invoke(source,root/'wrong-target',root/'wrong-backup',wrong,expect=1)
        assert not (root/'wrong-target').exists()
        print('Migrating complex credentials, Unicode, NULLs and duplicate commands',flush=True)
        result=invoke(source,destination,backups,envfile)
        for secret in (creds.password,creds.root_password): assert secret not in result.stdout+result.stderr
        assert tree_hash(runner,source)==before,'Original contents or ownership changed'
        summary=json.loads(next(backups.glob('*/summary.json')).read_text())
        assert summary['status']=='verified' and summary['verification']['tables']['clusterData']['rows']==3
        assert summary['phase']=='complete' and summary['failure'] is None and summary['cleanup']['status']=='completed'
        assert summary['verification']['tables']['clusterCommands']['rows']==2
        print('Checking real export failure and partial SQL import',flush=True)
        wrapper_dir=root/'test-bin';wrapper_dir.mkdir();wrapper=wrapper_dir/'docker'
        real_docker=shutil.which('docker')
        wrapper.write_text('#!'+sys.executable+'\n'+"""import os,subprocess,sys
args=sys.argv[1:]
fault=os.environ.get('DMS_FIXTURE_FAULT')
if fault=='export' and 'mysqldump' in args:
    sys.exit(41)
if fault=='partial-import' and any(arg.startswith('--init-command=') for arg in args):
    sql=b'USE smoke; CREATE TABLE partial_fixture(value INT); INSERT INTO partial_fixture VALUES (42); INVALID_FIXTURE_SQL;'
    sys.exit(subprocess.run(["""+repr(real_docker)+""",*args],input=sql).returncode)
os.execv("""+repr(real_docker)+""",["""+repr(real_docker)+""",*args])
""");wrapper.chmod(0o700)
        for fault in ('export','partial-import'):
            failed_target=root/(fault+'-target');failed_backups=root/(fault+'-backups')
            baseline=set(runner.run(['ps','-aq','--filter','label='+LABEL]).decode().split())
            failed_result=invoke(source,failed_target,failed_backups,envfile,expect=1,extra_env={'PATH':str(wrapper_dir)+os.pathsep+os.environ['PATH'],'DMS_FIXTURE_FAULT':fault})
            assert tree_hash(runner,source)==before,'Failed migration modified original'
            workspaces=list(failed_backups.glob('migration-*'))
            assert workspaces, fault+' failed before creating a workspace: '+failed_result.stderr+failed_result.stdout
            workspace=workspaces[0]
            failed_summary=json.loads((workspace/'summary.json').read_text())
            assert failed_summary['status']=='failed'
            assert failed_summary['phase']==('export_database' if fault=='export' else 'import_database')
            assert failed_summary['failure']['kind']=='operation_failed' and failed_summary['cleanup']['status']=='completed'
            assert (workspace/'application.sql').exists(),'Failure lost export artifact'
            assert set(runner.run(['ps','-aq','--filter','label='+LABEL]).decode().split())==baseline,'Failure leaked temporary containers'
            if fault=='export': assert not failed_target.exists()
            else:
                assert failed_target.exists()
                partial=DatabaseClient(runner,runner.start_target(failed_target,creds),creds);partial.ready()
                assert partial.query('SELECT value FROM smoke.partial_fixture;').strip()==b'42','Partial import data was not retained'
                runner.stop_clean(partial.container)
        print('Checking SIGINT and SIGTERM cleanup during target initialization',flush=True)
        for signum in (signal.SIGINT,signal.SIGTERM):
            interrupted_target=root/('interrupted-target-'+str(signum));interrupted_backups=root/('interrupted-backups-'+str(signum))
            process=subprocess.Popen([sys.executable,str(ROOT/'scripts/migrate_database.py'),'--source',str(source),
                '--destination',str(interrupted_target),'--backup-root',str(interrupted_backups),'--env-file',str(envfile),
                '--timeout-seconds','60'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                deadline=time.monotonic()+120
                while not interrupted_target.exists():
                    if process.poll() is not None: raise AssertionError('Interrupted test helper exited before target creation')
                    if time.monotonic()>deadline: raise AssertionError('Interrupted test target was not created')
                    time.sleep(0.05)
                process.send_signal(signum)
                stdout,stderr=process.communicate(timeout=90)
                assert process.returncode==130,'Interrupted helper did not exit 130'
                for secret in (creds.password,creds.root_password): assert secret not in stdout+stderr
                assert tree_hash(runner,source)==before,'Interrupted migration modified original'
                interrupted_summary=json.loads(next(interrupted_backups.glob('*/summary.json')).read_text())
                assert interrupted_summary['status']=='failed' and interrupted_summary['failure']['kind']=='interrupted'
                assert interrupted_summary['cleanup']['status']=='completed'
                for container in runner.run(['ps','-aq']).decode().split():
                    mounts=json.loads(runner.run(['inspect','--format','{{json .Mounts}}',container]))
                    assert not any(mount.get('Source','').startswith(str(interrupted_target)) or mount.get('Source','').startswith(str(interrupted_backups)) for mount in mounts),'Interrupted helper leaked a running container'
            finally:
                if process.poll() is None:
                    process.send_signal(signal.SIGTERM);process.communicate(timeout=90)
        # Original can still boot with the old image/credentials before resuming any writes.
        runner.run(['start',fixture]);DatabaseClient(runner,fixture,creds,legacy=True).ready()
        invoke(source,root/'running-target',root/'running-backup',envfile,expect=1)
        assert not (root/'running-backup').exists()
        runner.stop_clean(fixture)
        print('PASS: original preserved, verified logical restore, refusal paths and pre-resume rollback',flush=True)
    finally:
        runner.cleanup()
        # Only remove this generated test tree under the configured temporary parent, via an image utility that can read DB-owned files.
        assert root.parent==Path(tempfile.gettempdir()).resolve() and root.name.startswith('dms-migration-test-')
        _,owned=runner.owned_args('clean-fixture')
        runner.run(['run','--rm',*owned,'--user','0','--entrypoint','python','--mount',mount_spec(root,'/fixture'),PYTHON_IMAGE,'-c',
            "import pathlib,shutil; [(shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()) for p in pathlib.Path('/fixture').iterdir()]"])
        root.rmdir()

if __name__=='__main__': main()
