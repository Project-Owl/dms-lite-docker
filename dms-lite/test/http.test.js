const {test} = require('node:test');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {createApp} = require('../app');
const {serve, emptyDb} = require('./helpers');

test('importing the app has no database or listener side effects', () => {
  const result = spawnSync(process.execPath,['-e',"require('./app'); console.log('imported')"],{cwd:require('node:path').join(__dirname,'..'),timeout:2000,encoding:'utf8'});
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout.trim(), 'imported');
});

test('readiness reflects a database outage and errors never expose credentials', async t => {
  const db = emptyDb();
  const url = await serve(t,createApp({db}));
  assert.equal((await fetch(url+'/health/live')).status,200);
  assert.equal((await fetch(url+'/health/ready')).status,200);
  db.checkReady = async () => {throw new Error('password=topsecret');};
  const response = await fetch(url+'/health/ready');
  assert.equal(response.status,503);
  assert.equal((await response.text()).includes('topsecret'),false);
});

test('invalid message limits fail and query failures reach HTTP error handling', async t => {
  const db = emptyDb();
  const url = await serve(t,createApp({db}));
  for (const count of ['0','1001','1.5','abc']) {
    assert.equal((await fetch(url+'/data/getLastCount/'+count)).status,400);
  }
  db.getLastCount = async () => {throw new Error('password=topsecret');};
  const response = await fetch(url+'/ducks/getLastCount/12');
  assert.equal(response.status,503);
  assert.equal((await response.text()).includes('topsecret'),false);
});
test('unknown API paths return JSON errors rather than HTML',async t=>{
  const url=await serve(t,createApp({db:emptyDb()}));
  const response=await fetch(url+'/api/missing');
  assert.equal(response.status,404);
  assert.match(response.headers.get('content-type'),/application\/json/);
  assert.deepEqual(await response.json(),{error:'Not found'});
});
