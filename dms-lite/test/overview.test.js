const {test}=require('node:test');
const assert=require('node:assert/strict');
const {loadOverview,deviceState}=require('../routes/overview');
const now=Date.parse('2026-10-28T13:42:18Z');
const packet={timestamp:'2026-10-28T13:42:10Z',duck_id:'<img onerror=alert(1)>',topic:'sensor/temp',payload:'23.8'};
const db=()=>({getAllData:async()=>[packet],getDuckPlusData:async()=>[packet,{...packet,timestamp:'2026-10-28T12:00:00Z'}],getTopics:async()=>['sensor/temp','text']});
test('overview counts are actual loaded rows and message-derived freshness',async()=>{
 const result=await loadOverview(db(),300,now);
 assert.equal(result.loadedCount,1);assert.equal(result.deviceCount,2);assert.equal(result.recentCount,1);assert.equal(result.topicCount,2);
 assert.equal(result.latest,packet.timestamp);assert.equal(result.isEmpty,false);assert.equal(result.messages[0].duck_id,packet.duck_id);
});
test('overview keeps successful panels and never labels unavailable counts zero',async()=>{
 const result=await loadOverview({...db(),getAllData:async()=>{throw Error('private details');}},300,now);
 assert.equal(result.loadedCount,null);assert.equal(result.recentCount,1);assert.equal(result.errors.messages,true);assert.equal(result.isEmpty,false);
 assert.equal(JSON.stringify(result).includes('private details'),false);
});
test('overview empty state requires confirmed empty messages and devices',async()=>{
 const result=await loadOverview({getAllData:async()=>[],getDuckPlusData:async()=>[],getTopics:async()=>[]},300,now);
 assert.equal(result.isEmpty,true);assert.equal(result.latest,null);
 const failure=await loadOverview({getAllData:async()=>[],getDuckPlusData:async()=>{throw Error();},getTopics:async()=>[]},300,now);
 assert.equal(failure.isEmpty,false);assert.equal(failure.deviceCount,null);
});
test('invalid and future timestamps never claim recent connectivity',()=>{
 for(const value of [null,'bad','2027-01-01T00:00:00Z'])assert.equal(deviceState(value,300,now).recent,false);
 assert.equal(deviceState(packet.timestamp,300,now).recent,true);
 assert.equal(deviceState(packet.timestamp,300,now).ageText,'8 seconds ago');
});
