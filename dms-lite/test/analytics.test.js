const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createDatabase} = require('../routes/db');
const {createApp} = require('../app');
const {serve,emptyDb} = require('./helpers');
const records = [
  {timestamp:'2026-10-23 12:04:00',duck_id:'A',topic:'sensor/temp',payload:' '},
  {timestamp:'2026-10-23 12:03:00',duck_id:'A',topic:'sensor/temp',payload:'text'},
  {timestamp:'2026-10-23 12:02:00',duck_id:'B',topic:'sensor/temp',payload:'5.5'},
  {timestamp:'2026-10-23 12:01:00',duck_id:'A',topic:'sensor/temp',payload:'-2.5'},
  {timestamp:'2026-10-23 12:00:00',duck_id:'A',topic:'sensor/temp',payload:'1'},
];
test('analytics filters numeric samples, respects sample limit, and emits UTC in chronological order', async () => {
  let request;
  const db=createDatabase({query:async(sql,params) => {request={sql,params};return records;}});
  assert.deepEqual(await db.getReadings('sensor/temp',2),{samples:[
    {timestamp:'2026-10-23T12:01:00.000Z',value:-2.5},
    {timestamp:'2026-10-23T12:02:00.000Z',value:5.5}
  ]});
  assert.deepEqual(request.params,['sensor/temp']);
  assert.match(request.sql,/ORDER BY timestamp DESC LIMIT 1000/);
  assert.deepEqual(await db.getAlert('sensor/temp',-2.5,5.5),{reading:null});
  assert.deepEqual(await db.getAlert('sensor/temp',-2,5),{reading:{timestamp:'2026-10-23T12:02:00.000Z',duckId:'B',value:5.5}});
});
test('API serves typed empty and populated responses and supports slash topics', async t => {
  const requests=[];
  const db={...emptyDb(), getTopics:async()=>['sensor/temperature & humidity'], getUniqueDucks:async()=>[{duck_id:'D1'}],
    getReadings:async(topic,limit)=>{requests.push([topic,limit]); return {samples:[]};},
    getAlert:async()=>({reading:null}), getLatestByDuckId:async()=>({reading:null})};
  const url=await serve(t,createApp({db}));
  assert.deepEqual(await (await fetch(url+'/api/topics')).json(),['sensor/temperature & humidity']);
  assert.deepEqual(await (await fetch(url+'/api/ducks')).json(),['D1']);
  assert.deepEqual(await (await fetch(url+'/api/readings?topic=sensor%2Ftemperature%20%26%20humidity&limit=1')).json(),{samples:[]});
  assert.deepEqual(requests,[['sensor/temperature & humidity',1]]);
  assert.deepEqual(await (await fetch(url+'/api/alerts?topic=x&min=-2.5&max=5.5')).json(),{reading:null});
  assert.deepEqual(await (await fetch(url+'/api/ducks/D1/latest')).json(),{reading:null});
  for (const path of ['/api/readings','/api/readings?topic=x&limit=0','/api/readings?topic=x&limit=1001',
    '/api/readings?topic[]=x','/api/alerts?topic=x&min=9&max=1','/api/alerts?topic=x&min=&max=1',
    '/api/alerts?topic=x&min=NaN&max=1','/api/alerts?topic=x&min=0&max=Infinity']) {
    assert.equal((await fetch(url+path)).status,400,path);
  }
  db.getTopics=async()=>{throw new Error('database password secret');};
  const response=await fetch(url+'/api/topics');
  assert.equal(response.status,503);
  assert.deepEqual(await response.json(),{error:'Service unavailable. Please retry.'});
});
test('latest device query is ordered and converts timestamps, including absent devices',async()=>{
  let sql;
  const db=createDatabase({query:async(q,params)=>{sql=q; assert.deepEqual(params,['A']);return [records[0]];}});
  assert.deepEqual(await db.getLatestByDuckId('A'),{reading:{timestamp:'2026-10-23T12:04:00.000Z',topic:'sensor/temp',payload:' '}});
  assert.match(sql,/ORDER BY timestamp DESC LIMIT 1/);
  const empty=createDatabase({query:async()=>[]});
  assert.deepEqual(await empty.getReadings('x',100),{samples:[]});
  assert.deepEqual(await empty.getAlert('x',0,1),{reading:null});
  assert.deepEqual(await empty.getLatestByDuckId('A'),{reading:null});
  assert.deepEqual(await empty.getTopics(),[]);
});
