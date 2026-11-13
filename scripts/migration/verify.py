"""Stock application inventory and byte-preserving logical verification."""
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from .paths import MigrationError

TABLES={'clusterData':['timestamp','duck_id','topic','message_id','payload','path','hops','duck_type'],
        'clusterCommands':['timestamp','topic','payload']}
@dataclass(frozen=True)
class Credentials:
    database: str
    user: str
    password: str=field(repr=False)
    root_password: str=field(repr=False)

def identifier(value): return '`'+value.replace('`','``')+'`'
def literal(value): return "'"+value.replace("'","''")+"'"
def protected_file(path,mode='wb'):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    return os.fdopen(fd,mode)

class DatabaseClient:
    def __init__(self,runner,container,credentials,legacy=False):
        self.runner=runner;self.container=container;self.credentials=credentials;self.legacy=legacy
        self.client='mysql' if legacy else 'mariadb'
    def command(self,user='root'):
        return ['exec','--interactive','--env','MYSQL_PWD',self.container,self.client,'--protocol=TCP','--host=127.0.0.1',
                '--connect-timeout=5','--skip-ssl','--user='+user,'--batch','--raw','--skip-column-names']
    def query(self,sql,*,stdout=None,user='root'):
        password=self.credentials.root_password if user=='root' else self.credentials.password
        return self.runner.run(self.command(user),env={'MYSQL_PWD':password},input=("SET time_zone='+00:00'; "+sql).encode(),stdout=stdout,phase=('Legacy' if self.legacy else 'Target')+' database '+('administrator' if user=='root' else 'application')+' query')
    def json_rows(self,sql):
        return [json.loads(line) for line in self.query(sql).decode().splitlines() if line]
    def ready(self):
        deadline=time.monotonic()+self.runner.timeout
        admin='mysqladmin' if self.legacy else 'mariadb-admin'
        while time.monotonic()<deadline:
            try:
                self.runner.run(['exec',self.container,admin,'--protocol=TCP','-h127.0.0.1','--connect-timeout=2','ping','--silent'],phase='Database readiness')
                break
            except MigrationError: time.sleep(0.5)
        else: raise MigrationError('Temporary database did not become ready')
        # Authentication is checked once, not retried for ten minutes on a wrong password.
        self.query('SELECT 1;')
        self.query('USE '+identifier(self.credentials.database)+'; SELECT 1;',user=self.credentials.user)

    def dump(self,path):
        with protected_file(path) as output:
            self.runner.run(['exec','--env','MYSQL_PWD',self.container,'mysqldump','--protocol=TCP','--host=127.0.0.1',
                '--user=root','--single-transaction','--routines','--events','--triggers','--hex-blob',
                '--default-character-set=utf8mb4','--databases','--',self.credentials.database],
                env={'MYSQL_PWD':self.credentials.root_password},stdout=output,phase='Application database export')
        if not path.stat().st_size: raise MigrationError('Database export was empty')
    def restore(self,path,charset_defaults):
        for row in charset_defaults:
            if any(not re.fullmatch('[A-Za-z0-9_]+',value) for value in row.values()):
                raise MigrationError('Unsupported legacy charset defaults')
        mapping=','.join(row['charset']+'='+row['collation'] for row in charset_defaults)
        command=self.command()+['--init-command=SET SESSION character_set_collations='+literal(mapping)]
        with path.open('rb') as input_file:
            self.runner.run(command,env={'MYSQL_PWD':self.credentials.root_password},stdin=input_file,phase='Application database import')

def validate_inventory(value,credentials,official=False):
    if {table['name'] for table in value['tables']} != set(TABLES) or any(table['engine']!='InnoDB' for table in value['tables']):
        raise MigrationError('Custom tables or engines require the manual migration procedure')
    allowed={'root','mysql','mariadb.sys',credentials.user}
    if official: allowed.add('healthcheck')
    for account in value['accounts']:
        if account['user'] not in allowed or (account['user']==credentials.user and (account['host']!='%' or account.get('plugin')!='mysql_native_password')):
            raise MigrationError('Custom accounts require the manual migration procedure')
    if value['objects']:
        raise MigrationError('Custom triggers, routines or events require manual definer/grant review')
    grants=value['grants'];expected='GRANT ALL PRIVILEGES ON '+identifier(credentials.database)+'.* TO '
    if not any(grant.startswith(expected) for grant in grants):
        raise MigrationError('Custom application grants require the manual migration procedure')
    if any((not grant.startswith(('GRANT USAGE ON *.* TO ',expected))) or 'WITH GRANT OPTION' in grant or 'REQUIRE ' in grant for grant in grants):
        raise MigrationError('Custom application grants require the manual migration procedure')

def validate_columns(columns):
    for column in columns:
        table,name,kind=column['table'],column['name'],column['type'].lower()
        if table=='clusterData' and name=='timestamp':
            valid=bool(re.fullmatch(r'(datetime|timestamp)(\(\d\))?',kind))
        elif name in ('hops','duck_type'):
            valid=bool(re.fullmatch(r'(int|integer|bigint)(\(\d+\))?( unsigned)?( zerofill)?',kind))
        else:
            capacity={'tinytext':255,'text':65535,'mediumtext':16777215,'longtext':4294967295}.get(kind,0)
            match=re.fullmatch(r'(?:var)?char\((\d+)\)',kind)
            if match: capacity=int(match[1])
            minimum=65535 if table=='clusterData' else {'timestamp':24,'topic':7,'payload':1025}[name]
            valid=capacity>=minimum
        if not valid: raise MigrationError('Incompatible table column types or capacities require manual migration')

def inventory(client):
    schema=literal(client.credentials.database)
    tables=client.json_rows("SELECT JSON_OBJECT('name',TABLE_NAME,'engine',ENGINE,'collation',TABLE_COLLATION) FROM information_schema.TABLES WHERE TABLE_SCHEMA="+schema+' ORDER BY TABLE_NAME;')
    accounts=client.json_rows("SELECT JSON_OBJECT('user',User,'host',Host,'plugin',plugin) FROM mysql.user ORDER BY User,Host;")
    objects=client.json_rows("SELECT JSON_OBJECT('name',TRIGGER_NAME) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA="+schema+';')
    objects+=client.json_rows("SELECT JSON_OBJECT('name',ROUTINE_NAME) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA="+schema+';')
    objects+=client.json_rows("SELECT JSON_OBJECT('name',EVENT_NAME) FROM information_schema.EVENTS WHERE EVENT_SCHEMA="+schema+';')
    grants=client.query('SHOW GRANTS FOR '+identifier(client.credentials.user)+'@`%`;').decode().splitlines()
    value={'tables':tables,'accounts':accounts,'objects':objects,'grants':grants}
    validate_inventory(value,client.credentials,official=not client.legacy)
    columns=client.json_rows("SELECT JSON_OBJECT('table',TABLE_NAME,'name',COLUMN_NAME,'type',COLUMN_TYPE,'nullable',IS_NULLABLE,'default',COLUMN_DEFAULT,'extra',EXTRA,'charset',CHARACTER_SET_NAME,'collation',COLLATION_NAME) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA="+schema+' ORDER BY TABLE_NAME,ORDINAL_POSITION;')
    for table,names in TABLES.items():
        actual=[column['name'] for column in columns if column['table']==table]
        if actual!=names: raise MigrationError('Custom table columns require the manual migration procedure')
    validate_columns(columns)
    database=client.json_rows("SELECT JSON_OBJECT('charset',DEFAULT_CHARACTER_SET_NAME,'collation',DEFAULT_COLLATION_NAME) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME="+schema+';')[0]
    return {'tables':tables,'columns':columns,'database':database}

def canonical_schema(value):
    normalized=json.loads(json.dumps(value))
    def normalize(item):
        if isinstance(item,dict): return {key:normalize(value) for key,value in item.items()}
        if isinstance(item,list): return [normalize(value) for value in item]
        if isinstance(item,str):
            item=re.sub(r'^(tinyint|smallint|mediumint|int|bigint)\(\d+\)',r'\1',item)
            if item=='utf8': return 'utf8mb3'
            if item.startswith('utf8_'): return 'utf8mb3_'+item[5:]
        return item
    return normalize(normalized)

def fingerprint(client,workspace,label):
    schema=inventory(client)
    with protected_file(workspace/(label+'-schema.json'),'w') as output:
        json.dump(canonical_schema(schema),output,sort_keys=True,indent=2)
    result={'schema':hashlib.sha256(json.dumps(canonical_schema(schema),sort_keys=True).encode()).hexdigest(),'tables':{}}
    for table,names in TABLES.items():
        fields=["IF("+identifier(name)+" IS NULL,'N',CONCAT('V',HEX(CAST("+identifier(name)+" AS BINARY))))" for name in names]
        sql='SELECT CONCAT_WS(CHAR(9),'+','.join(fields)+') AS encoded_row FROM '+identifier(client.credentials.database)+'.'+identifier(table)+' ORDER BY BINARY encoded_row;'
        path=workspace/(label+'-'+table+'.rows')
        with protected_file(path) as output: client.query(sql,stdout=output)
        digest=hashlib.sha256();count=0
        with path.open('rb') as source:
            for line in source: digest.update(line);count+=1
        result['tables'][table]={'rows':count,'digest':digest.hexdigest()}
    return result,schema

def compare_verifications(source,target):
    if source!=target: raise MigrationError('Restored schema or row-content verification failed; destination retained')
