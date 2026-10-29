const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createApp}=require('../app');
const {serve,emptyDb}=require('./helpers');
const post=(url,id)=>fetch(url+'/ducks/postEnableWiFi',{method:'POST',redirect:'manual',headers:{'content-type':'application/x-www-form-urlencoded'},body:new URLSearchParams({duck_id:id})});
test('WiFi-only deployment rejects commands and enabled commands require an ID',async t=>{
  const disabled=await serve(t,createApp({db:emptyDb()}));
  assert.equal((await post(disabled,'D1')).status,409);
  const enabled=await serve(t,createApp({db:emptyDb(),commandsEnabled:true}));
  assert.equal((await post(enabled,'')).status,400);
});
test('queue response waits for database commit and failure is not a success redirect',{timeout:3000},async t=>{
  let finish,entered;
  const gate=new Promise(resolve=>{finish=resolve;});
  const start=new Promise(resolve=>{entered=resolve;});
  const db={...emptyDb(),postCommand:async(topic,payload)=>{assert.equal(topic,' /wifi/');assert.equal(payload,'1D1');entered();await gate;}};
  const url=await serve(t,createApp({db,commandsEnabled:true}));
  let resolved=false;
  const pending=post(url,'D1').then(response=>{resolved=true;return response;});
  await start;
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(resolved,false);
  finish();
  const response=await pending;
  assert.equal(response.status,303);
  assert.match(response.headers.get('location'),/queued/);
  db.postCommand=async()=>{throw new Error('database offline');};
  assert.equal((await post(url,'D1')).status,503);
});
test('browser commands reject cross-site origins before queueing',async t=>{
  let queued=0;
  const url=await serve(t,createApp({db:{...emptyDb(),postCommand:async()=>{queued++;}},commandsEnabled:true}));
  const response=await fetch(url+'/ducks/postEnableWiFi',{method:'POST',redirect:'manual',headers:{origin:'https://untrusted.example','content-type':'application/x-www-form-urlencoded'},body:'duck_id=D1'});
  assert.equal(response.status,403);
  assert.equal(queued,0);
});
test('missing, unsupported and malformed command bodies produce client errors',async t=>{
  const url=await serve(t,createApp({db:emptyDb(),commandsEnabled:true}));
  for(const options of [
    {}, {headers:{'content-type':'text/plain'},body:'duck_id=D1'},
    {headers:{'content-type':'application/json'},body:'{'},
    {headers:{'content-type':'application/json'},body:'null'}
  ]) assert.equal((await fetch(url+'/ducks/postEnableWiFi',{method:'POST',...options})).status,400);
});
