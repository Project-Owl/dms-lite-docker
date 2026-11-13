#!/usr/bin/env python3
"""Explicit, copy-only migration from stock LinuxServer MariaDB 10.5."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.migration.paths import MigrationError,plan_paths,assert_stopped
from scripts.migration.docker import DockerRunner,LEGACY_IMAGE,TARGET_IMAGE
from scripts.migration.verify import Credentials,DatabaseClient,inventory,fingerprint,compare_verifications,protected_file,identifier

def load_credentials(runner,env_file):
    if not env_file.is_file(): raise MigrationError('Environment file is missing')
    config=json.loads(runner.run(['compose','--env-file',str(env_file),'-f',str(ROOT/'docker-compose-base.yml'),'config','--format','json'],phase='Configuration loading'))
    web=config['services']['web']['environment'];db=config['services']['mariadb']['environment']
    values=[web.get('MYSQL_DATABASE'),web.get('MYSQL_USER'),web.get('MYSQL_PASSWORD'),db.get('MARIADB_ROOT_PASSWORD')]
    if not all(isinstance(value,str) and value for value in values): raise MigrationError('Required MYSQL settings are missing')
    if any(not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]{0,63}',value) for value in values[:2]):
        raise MigrationError('Custom database/account names require the manual migration procedure')
    if values[0] in ('mysql','sys','information_schema','performance_schema') or values[1] in ('root','mysql','mariadb.sys'):
        raise MigrationError('Use a dedicated application database and non-system application account')
    # Compose serializes literal dollars doubled so its output can be interpolated again.
    return Credentials(*(value.replace('$$','$') for value in values))

def run_migration(paths,credentials,runner,*,client_factory=DatabaseClient):
    runner.assert_local();assert_stopped(paths,runner)
    # Revalidate just before the first filesystem writes.
    paths=plan_paths(paths.source,paths.destination,paths.backup_root)
    paths.backup_root.mkdir(parents=True,exist_ok=True)
    workspace=Path(tempfile.mkdtemp(prefix='migration-',dir=paths.backup_root));workspace.chmod(0o700)
    summary={'status':'failed','source':str(paths.source),'destination':str(paths.destination),
        'workspace':str(workspace),'source_image':LEGACY_IMAGE,'target_image':TARGET_IMAGE,
        'phase':'copy_source','failure':None,'cleanup':{'status':'pending'}}
    try:
        copy=runner.copy_source(paths.source,workspace)
        summary['phase']='start_source'
        source=client_factory(runner,runner.start_source(copy),credentials,legacy=True)
        summary['phase']='authenticate_source';source.ready()
        summary['phase']='inspect_source'
        before,schema=fingerprint(source,workspace,'source')
        charset_defaults=source.json_rows("SELECT JSON_OBJECT('charset',CHARACTER_SET_NAME,'collation',DEFAULT_COLLATE_NAME) FROM information_schema.CHARACTER_SETS ORDER BY CHARACTER_SET_NAME;")
        used_charsets={schema['database']['charset'],*(column['charset'] for column in schema.get('columns',[]) if column['charset'])}
        charset_defaults=[row for row in charset_defaults if row['charset'] in used_charsets]
        summary['phase']='export_database'
        dump=workspace/'application.sql';source.dump(dump)
        # No source account provisioning or target creation precedes the inventory checks.
        summary['phase']='prepare_target'
        plan_paths(paths.source,paths.destination,paths.backup_root)
        assert_stopped(paths,runner)
        paths.destination.mkdir(parents=True,exist_ok=True,mode=0o700)
        summary['phase']='start_target'
        target=client_factory(runner,runner.start_target(paths.destination,credentials),credentials)
        summary['phase']='authenticate_target';target.ready()
        summary['phase']='configure_target'
        metadata=schema['database']
        for value in metadata.values():
            if not re.fullmatch('[A-Za-z0-9_]+',value): raise MigrationError('Unsupported charset/collation metadata')
        target.query('ALTER DATABASE '+identifier(credentials.database)+' CHARACTER SET '+metadata['charset']+' COLLATE '+metadata['collation']+';')
        summary['phase']='import_database'
        target.restore(dump,charset_defaults)
        summary['phase']='verify_target'
        after,_=fingerprint(target,workspace,'target');compare_verifications(before,after)
        summary['phase']='shutdown'
        runner.stop_clean(target.container);runner.stop_clean(source.container)
        summary.update(status='verified',phase='complete',verification=after)
        return summary
    except (Exception,KeyboardInterrupt) as error:
        kind='interrupted' if isinstance(error,KeyboardInterrupt) else 'operation_failed' if isinstance(error,MigrationError) else 'unexpected_error'
        summary['failure']={'kind':kind,'phase':summary['phase']}
        raise
    finally:
        try:
            runner.cleanup()
            summary['cleanup']={'status':'completed'}
        except (Exception,KeyboardInterrupt):
            summary['status']='failed'
            summary['cleanup']={'status':'failed','message':'Temporary-container cleanup could not be confirmed. Inspect migration-labelled containers before retrying.'}
            if summary['failure'] is None:
                summary['phase']='cleanup'
                summary['failure']={'kind':'cleanup_failed','phase':'cleanup'}
            raise
        finally:
            with protected_file(workspace/'summary.json','w') as output: json.dump(summary,output,indent=2)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'data')
    parser.add_argument('--destination',type=Path,default=ROOT/'data-mariadb')
    parser.add_argument('--backup-root',type=Path,default=ROOT/'backups')
    parser.add_argument('--env-file',type=Path,default=ROOT/'.env')
    parser.add_argument('--timeout-seconds',type=int,default=600)
    args=parser.parse_args()
    if args.timeout_seconds<1: parser.error('timeout must be positive')
    def interrupted(*_): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,interrupted)
    try:
        paths=plan_paths(args.source,args.destination,args.backup_root)
        runner=DockerRunner(args.timeout_seconds)
        runner.assert_local();assert_stopped(paths,runner)
        credentials=load_credentials(runner,args.env_file.resolve())
        result=run_migration(paths,credentials,runner)
        print('Migration verified. Summary: '+result['workspace']+'/summary.json')
        print('Original data is unchanged. Start the new stack separately when ready.')
        return 0
    except KeyboardInterrupt:
        print('Migration interrupted; original and any partial destination are retained.',file=sys.stderr);return 130
    except MigrationError as error:
        print(str(error),file=sys.stderr);return 1
    except Exception:
        print('Migration failed unexpectedly; original and any partial destination are retained.',file=sys.stderr);return 1

if __name__=='__main__': sys.exit(main())
