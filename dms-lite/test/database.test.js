const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createDatabase} = require('../routes/db');

test('database binds a device and count as scalars and preserves query errors', async () => {
  const queries = [];
  const db = createDatabase({query: async (sql, params) => {
    queries.push({sql, params});
    if (params?.[0] === 'broken') throw new Error('database unavailable');
    return [];
  }});
  await db.getDataByDuckId('DUCK01');
  await db.getLastCount(12);
  assert.deepEqual(queries.map(q => q.params), [['DUCK01'], [12]]);
  await assert.rejects(db.getDataByDuckId('broken'), /database unavailable/);
});

test('initialization releases its connection without swallowing a DDL failure', async () => {
  let released = false;
  const db = createDatabase({getConnection: async () => ({
    query: async () => {throw new Error('DDL failed');},
    release: () => {released = true;}
  })});
  await assert.rejects(db.initialize(), /DDL failed/);
  assert.equal(released, true);
});

test('initialization accepts existing columns without altering or deleting rows', async () => {
  const columns = {clusterData: ['timestamp','duck_id','topic','message_id','payload','path','hops','duck_type'], clusterCommands:['timestamp','topic','payload']};
  const statements = [];
  const db = createDatabase({getConnection: async () => ({
    query: async (sql) => {
      statements.push(sql);
      const table = Object.keys(columns).find(t => sql.includes(t));
      return sql.startsWith('SHOW') ? columns[table].map(Field => ({Field,Type:Field==='timestamp'&&table==='clusterData'?'datetime': ['hops','duck_type'].includes(Field)?'int(11)':'text',Null:'YES',Default:null,Extra:''})) : [];
    }, release() {}
  })});
  await db.initialize();
  assert.equal(statements.filter(sql => sql.startsWith('CREATE TABLE IF NOT EXISTS')).length, 2);
  assert.equal(statements.some(sql => /\b(ALTER|DELETE|DROP|TRUNCATE)\b/.test(sql)), false);
});
test('schema checks reject incompatible capacities, types and required extra columns',async()=>{
  const data=['timestamp','duck_id','topic','message_id','payload','path','hops','duck_type'].map(Field=>({Field,Type:Field==='timestamp'?'datetime':['hops','duck_type'].includes(Field)?'int(11)':'text',Null:'YES',Default:null,Extra:''}));
  const commands=['timestamp','topic','payload'].map(Field=>({Field,Type:'text',Null:'YES',Default:null,Extra:''}));
  for(const [field,type] of [['payload','int(11)'],['duck_id','varchar(8)'],['timestamp','text'],['hops','smallint(6)'],['extra','int(11)']]) {
    const changed=data.map(row=>row.Field===field?{...row,Type:type}:row);
    if(field==='extra')changed.push({Field:'extra',Type:type,Null:'NO',Default:null,Extra:''});
    const db=createDatabase({getConnection:async()=>({query:async sql=>sql.startsWith('SHOW')?(sql.includes('clusterData')?changed:commands):[],release(){}})});
    await assert.rejects(db.initialize(),error=>{
      assert.match(error.message,new RegExp('clusterData.*'+field));
      assert.equal(error.code,'SCHEMA_INCOMPATIBLE');return true;
    });
  }
});

test('incompatible existing schema stops initialization', async () => {
  const db = createDatabase({getConnection: async () => ({
    query: async sql => sql.startsWith('SHOW') ? [{Field:'timestamp'}] : [], release() {}
  })});
  await assert.rejects(db.initialize(), /schema|column/i);
});
test('connector BigInt fields retain precision and insert metadata stays out of responses',async()=>{
  const db=createDatabase({query:async sql=>sql.startsWith('INSERT')?{insertId:9007199254740993n}:[{timestamp:'2026-10-23 12:00:00',hops:2n,duck_type:9007199254740993n}]});
  assert.deepEqual(await db.getAllData(),[{timestamp:'2026-10-23T12:00:00.000Z',hops:2,duck_type:'9007199254740993'}]);
  assert.equal(await db.postCommand(' /wifi/','1D1'),undefined);
});
