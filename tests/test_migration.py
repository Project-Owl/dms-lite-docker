import os
import pathlib
import subprocess
import tempfile
import unittest
from scripts.migration.paths import MigrationError, plan_paths, assert_stopped
from scripts.migration.docker import DockerRunner

class PathTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name);self.source=self.root/'old data'
        (self.source/'databases/mysql').mkdir(parents=True)
        (self.source/'databases/ibdata1').write_bytes(b'original')
        self.dest=self.root/'new data';self.backup=self.root/'backup'
    def test_valid_preflight_performs_no_filesystem_writes(self):
        paths=plan_paths(self.source,self.dest,self.backup)
        self.assertEqual(paths.source,self.source)
        self.assertFalse(self.dest.exists());self.assertFalse(self.backup.exists())
        self.assertEqual((self.source/'databases/ibdata1').read_bytes(),b'original')
    def test_invalid_paths_refuse_without_overwrite(self):
        self.dest.mkdir();(self.dest/'keep').write_text('keep')
        for source,dest,backup in [(self.root/'missing',self.dest,self.backup),(pathlib.Path('/'),self.dest,self.backup),(self.source,self.source,self.backup),(self.source,self.source/'nested',self.backup),(self.source,self.dest,self.backup),(self.source,self.root/'empty',self.source/'backup')]:
            with self.assertRaises(MigrationError): plan_paths(source,dest,backup)
        self.assertEqual((self.dest/'keep').read_text(),'keep')
        self.assertFalse(self.backup.exists())
    def test_symlink_alias_is_refused(self):
        alias=self.root/'alias';alias.symlink_to(self.source,target_is_directory=True)
        with self.assertRaises(MigrationError): plan_paths(alias,self.dest,self.backup)
        parent=self.root/'link';parent.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(MigrationError): plan_paths(self.source,parent/'new',self.backup)
    def test_running_mount_rejected_before_working_copy(self):
        paths=plan_paths(self.source,self.dest,self.backup)
        class Runner:
            def running_mounts(_): return [self.source]
        with self.assertRaises(MigrationError): assert_stopped(paths,Runner())
        self.assertFalse(self.backup.exists())

class RunnerTests(unittest.TestCase):
    def test_timeout_and_errors_do_not_disclose_credentials(self):
        secret='secret # quote " $(no)'
        def fail(*args,**kwargs): raise subprocess.TimeoutExpired(args[0],1)
        runner=DockerRunner(timeout=1,execute=fail)
        with self.assertRaises(MigrationError) as raised: runner.run(['info'],env={'MYSQL_PWD':secret})
        self.assertNotIn(secret,str(raised.exception))
    def test_cleanup_checks_ownership_before_deleting(self):
        calls=[]
        def execute(args,**kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args,0,b'foreign\n',b'')
        runner=DockerRunner(execute=execute);runner.containers.add('foreign-container')
        runner.cleanup()
        self.assertFalse(any('rm' in args for args in calls))


class InventoryTests(unittest.TestCase):
    def test_custom_accounts_objects_and_grants_require_manual_migration(self):
        from scripts.migration.verify import Credentials, validate_inventory
        creds=Credentials('app','app','password # $(x)','root secret')
        base={'tables':[{'name':'clusterCommands','engine':'InnoDB'},{'name':'clusterData','engine':'InnoDB'}],
              'accounts':[{'user':'root','host':'localhost','plugin':'mysql_native_password'},{'user':'app','host':'%','plugin':'mysql_native_password'}],
              'grants':['GRANT USAGE ON *.* TO `app`@`%`','GRANT ALL PRIVILEGES ON `app`.* TO `app`@`%`'],
              'objects':[]}
        validate_inventory(base,creds)
        for changes in [{'accounts':base['accounts']+[{'user':'custom','host':'%'}]},
                        {'objects':[{'name':'trigger','definer':'unknown@%'}]},
                        {'grants':['GRANT SELECT ON `app`.* TO `app`@`%`']}]:
            with self.assertRaises(MigrationError): validate_inventory({**base,**changes},creds)
        self.assertNotIn('password #',repr(creds));self.assertNotIn('root secret',repr(creds))
    def test_comparison_rejects_mismatched_data_or_schema(self):
        from scripts.migration.verify import compare_verifications
        value={'schema':'a','tables':{'clusterData':{'rows':2,'digest':'b'}}}
        compare_verifications(value,value)
        with self.assertRaises(MigrationError): compare_verifications(value,{'schema':'c','tables':value['tables']})
        with self.assertRaises(MigrationError): compare_verifications(value,{'schema':'a','tables':{'clusterData':{'rows':1,'digest':'b'}}})

class OwnedMountTests(unittest.TestCase):
    def test_runner_ignores_only_its_own_temporary_mounts(self):
        import json
        runner=None
        def execute(args,**kwargs):
            if args[1:]==['ps','-q']: output=b'own\nother\n'
            elif '.Config.Labels' in ' '.join(args): output=(runner.run_id if args[-1]=='own' else 'foreign').encode()
            else: output=json.dumps([{'Source':'/tmp/owned' if args[-1]=='own' else '/tmp/operator'}]).encode()
            return subprocess.CompletedProcess(args,0,output,b'')
        runner=DockerRunner(execute=execute)
        self.assertEqual(runner.running_mounts(),['/tmp/operator'])

class FailureTests(unittest.TestCase):
    def test_import_failure_and_interruption_preserve_data_and_cleanup(self):
        import shutil
        from unittest.mock import patch
        from scripts.migrate_database import run_migration
        from scripts.migration.verify import Credentials
        for failure in (MigrationError('Import failed'),KeyboardInterrupt()):
            with tempfile.TemporaryDirectory() as tmp:
                root=pathlib.Path(tmp);source=root/'source';(source/'databases/mysql').mkdir(parents=True)
                original=source/'databases/data';original.write_bytes(b'original')
                paths=plan_paths(source,root/'target',root/'backups')
                class Runner:
                    cleaned=False
                    def assert_local(self): pass
                    def running_mounts(self): return []
                    def copy_source(self,source,workspace):
                        target=workspace/'copy';shutil.copytree(source,target);return target
                    def start_source(self,copy): return 'source'
                    def start_target(self,dest,creds): (dest/'partial').write_bytes(b'partial');return 'target'
                    def cleanup(self): self.cleaned=True
                class Client:
                    def __init__(self,runner,container,creds,legacy=False): self.container=container
                    def ready(self): pass
                    def dump(self,path): path.write_bytes(b'export');path.chmod(0o600)
                    def query(self,sql): pass
                    def json_rows(self,sql): return []
                    def restore(self,path,*args): raise failure
                runner=Runner()
                with patch('scripts.migrate_database.fingerprint',return_value=({'schema':'same','tables':{}},{'database':{'charset':'utf8mb4','collation':'utf8mb4_general_ci'}})):
                    with self.assertRaises(type(failure)): run_migration(paths,Credentials('app','app','pw','root'),runner,client_factory=Client)
                self.assertEqual(original.read_bytes(),b'original')
                self.assertEqual((paths.destination/'partial').read_bytes(),b'partial')
                self.assertTrue(runner.cleaned)
                summaries=list(paths.backup_root.glob('*/summary.json'));self.assertEqual(len(summaries),1)
                self.assertEqual(summaries[0].stat().st_mode&0o777,0o600)
                import json
                summary=json.loads(summaries[0].read_text())
                self.assertEqual(summary['phase'],'import_database')
                self.assertEqual(summary['failure']['kind'],'interrupted' if isinstance(failure,KeyboardInterrupt) else 'operation_failed')
                self.assertEqual(summary['cleanup']['status'],'completed')

class InternalAliasTests(unittest.TestCase):
    def test_legacy_databases_cannot_escape_through_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);source=root/'source';source.mkdir()
            external=root/'external';(external/'mysql').mkdir(parents=True)
            (source/'databases').symlink_to(external,target_is_directory=True)
            with self.assertRaises(MigrationError): plan_paths(source,root/'target',root/'backups')

class QueryTransportTests(unittest.TestCase):
    def test_query_keeps_docker_stdin_open_for_sql(self):
        from scripts.migration.verify import Credentials, DatabaseClient
        calls=[]
        def execute(args,**kwargs):
            calls.append((args,kwargs))
            return subprocess.CompletedProcess(args,0,b'1\n',b'')
        runner=DockerRunner(execute=execute)
        client=DatabaseClient(runner,'test-owned',Credentials('app','app','pw','rootpw'))
        self.assertEqual(client.query('SELECT 1;'),b'1\n')
        args,kwargs=calls[0]
        self.assertIn('--interactive',args)
        self.assertIn(b'SELECT 1;',kwargs['input'])

class CredentialTests(unittest.TestCase):
    def test_compose_rendered_dollars_are_decoded_once(self):
        import json
        from scripts.migrate_database import load_credentials
        from scripts.migration.verify import Credentials
        expected=Credentials('app','app',"quote' $$(text)",'root # " $(text)')
        config={'services':{'web':{'environment':{'MYSQL_DATABASE':expected.database,'MYSQL_USER':expected.user,'MYSQL_PASSWORD':expected.password.replace('$','$$')}},'mariadb':{'environment':{'MARIADB_ROOT_PASSWORD':expected.root_password.replace('$','$$')}}}}
        class Runner:
            def run(self,*args,**kwargs): return json.dumps(config).encode()
        with tempfile.TemporaryDirectory() as tmp:
            env=pathlib.Path(tmp)/'env';env.touch()
            self.assertEqual(load_credentials(Runner(),env),expected)

class CollationTests(unittest.TestCase):
    def test_restore_uses_legacy_charset_defaults_in_import_session(self):
        from scripts.migration.verify import Credentials, DatabaseClient
        calls=[]
        def execute(args,**kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args,0,b'',b'')
        with tempfile.TemporaryDirectory() as tmp:
            dump=pathlib.Path(tmp)/'app.sql';dump.write_text('SELECT 1;')
            client=DatabaseClient(DockerRunner(execute=execute),'target',Credentials('app','app','pw','root'))
            client.restore(dump,[{'charset':'utf8mb4','collation':'utf8mb4_general_ci'}])
        self.assertIn("--init-command=SET SESSION character_set_collations='utf8mb4=utf8mb4_general_ci'",calls[0])

class ReviewRegressionTests(unittest.TestCase):
    def test_cleanup_reports_unavailable_daemon(self):
        def execute(args,**kwargs): return subprocess.CompletedProcess(args,1,b'',b'Cannot connect to Docker')
        runner=DockerRunner(execute=execute);runner.containers.add('owned')
        with self.assertRaises(MigrationError): runner.cleanup()
    def test_schema_rejects_incompatible_types_and_capacities(self):
        from scripts.migration.verify import TABLES,validate_columns
        columns=[{'table':table,'name':name,'type':'datetime' if table=='clusterData' and name=='timestamp' else 'int(11)' if name in ('hops','duck_type') else 'text'} for table,names in TABLES.items() for name in names]
        validate_columns(columns)
        for bad in ('int','varchar(8)'):
            invalid=[{**column,'type':bad} if column['name']=='payload' and column['table']=='clusterData' else column for column in columns]
            with self.assertRaises(MigrationError): validate_columns(invalid)

class SchemaPreflightTests(unittest.TestCase):
    def test_incompatible_schema_never_creates_target(self):
        from scripts.migrate_database import run_migration
        from scripts.migration.verify import TABLES,Credentials
        import shutil
        class Runner:
            def assert_local(self): pass
            def running_mounts(self): return []
            def copy_source(self,source,workspace):
                result=workspace/'copy';shutil.copytree(source,result);return result
            def start_source(self,copy): return 'source'
            def start_target(self,*args): raise AssertionError('Target must not start')
            def cleanup(self): pass
        class Client:
            def __init__(self,*args,**kwargs): self.credentials=Credentials('app','app','pw','root');self.legacy=True
            def ready(self): pass
            def query(self,sql): return b'GRANT ALL PRIVILEGES ON `app`.* TO `app`@`%`\n'
            def json_rows(self,sql):
                if 'information_schema.TABLES ' in sql: return [{'name':table,'engine':'InnoDB'} for table in TABLES]
                if 'mysql.user' in sql: return [{'user':'app','host':'%','plugin':'mysql_native_password'}]
                if 'information_schema.COLUMNS ' in sql: return [{'table':table,'name':name,'type':'int'} for table,names in TABLES.items() for name in names]
                return []
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);source=root/'source';(source/'databases/mysql').mkdir(parents=True)
            paths=plan_paths(source,root/'target',root/'backups')
            with self.assertRaises(MigrationError): run_migration(paths,Credentials('app','app','pw','root'),Runner(),client_factory=Client)
            self.assertFalse(paths.destination.exists())

class SummaryTests(unittest.TestCase):
    def test_summaries_record_safe_phase_and_cleanup_outcome(self):
        import json
        from scripts.migrate_database import run_migration
        from scripts.migration.verify import Credentials
        secret='root-password-never-record'
        for cleanup_fails in (False,True):
            with tempfile.TemporaryDirectory() as tmp:
                root=pathlib.Path(tmp);source=root/'source';(source/'databases/mysql').mkdir(parents=True)
                paths=plan_paths(source,root/'target',root/'backups')
                class Runner:
                    def assert_local(self): pass
                    def running_mounts(self): return []
                    def copy_source(self,*args): raise RuntimeError(secret)
                    def cleanup(self):
                        if cleanup_fails: raise MigrationError(secret)
                with self.assertRaises((RuntimeError,MigrationError)):
                    run_migration(paths,Credentials('app','app','pw',secret),Runner())
                summary=json.loads(next(paths.backup_root.glob('*/summary.json')).read_text())
                self.assertEqual(summary['phase'],'copy_source')
                self.assertEqual(summary['failure']['kind'],'unexpected_error')
                self.assertEqual(summary['cleanup']['status'],'failed' if cleanup_fails else 'completed')
                self.assertNotIn(secret,json.dumps(summary))

class SuccessfulCleanupFailureTests(unittest.TestCase):
    def test_verified_data_is_not_reported_successful_when_cleanup_fails(self):
        import json
        from unittest.mock import patch
        from scripts.migrate_database import run_migration
        from scripts.migration.verify import Credentials
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);source=root/'source';(source/'databases/mysql').mkdir(parents=True)
            paths=plan_paths(source,root/'target',root/'backups')
            class Runner:
                def assert_local(self): pass
                def running_mounts(self): return []
                def copy_source(self,source,workspace): return workspace/'copy'
                def start_source(self,copy): return 'source'
                def start_target(self,*args): return 'target'
                def stop_clean(self,*args): pass
                def cleanup(self): raise MigrationError('private cleanup detail')
            class Client:
                def __init__(self,runner,container,*args,**kwargs): self.container=container
                def ready(self): pass
                def dump(self,path): path.write_bytes(b'export')
                def json_rows(self,sql): return []
                def query(self,sql): pass
                def restore(self,*args): pass
            fingerprint=({'schema':'same','tables':{}},{'database':{'charset':'utf8mb4','collation':'utf8mb4_general_ci'}})
            with patch('scripts.migrate_database.fingerprint',return_value=fingerprint):
                with self.assertRaises(MigrationError): run_migration(paths,Credentials('app','app','pw','root'),Runner(),client_factory=Client)
            summary=json.loads(next(paths.backup_root.glob('*/summary.json')).read_text())
            self.assertEqual(summary['status'],'failed');self.assertEqual(summary['phase'],'cleanup')
            self.assertEqual(summary['failure']['kind'],'cleanup_failed')
            self.assertEqual(summary['cleanup']['status'],'failed')
            self.assertNotIn('private cleanup detail',json.dumps(summary))

if __name__=='__main__': unittest.main()
