const {test}=require('node:test');
const assert=require('node:assert/strict');
test('charts align timestamps without replacing missing samples with zero',async()=>{
  const {alignSeries}=await import('../public/new-js/chart-data.mjs');
  assert.deepEqual(alignSeries([{label:'A',samples:[{timestamp:'2026-10-23T12:00:00.000Z',value:2}]},{label:'B',samples:[{timestamp:'2026-10-23T12:01:00.000Z',value:-1.5}]}]),{
    labels:['2026-10-23T12:00:00.000Z','2026-10-23T12:01:00.000Z'],datasets:[{label:'A',data:[2,null]},{label:'B',data:[null,-1.5]}]
  });
});
test('chart alignment preserves every sample sharing a whole-second timestamp',async()=>{
  const {alignSeries}=await import('../public/new-js/chart-data.mjs');
  const t='2026-10-23T12:00:00.000Z',next='2026-10-23T12:00:01.000Z';
  assert.deepEqual(alignSeries([
    {label:'A',samples:[{timestamp:t,value:1},{timestamp:t,value:9}]},
    {label:'B',samples:[{timestamp:t,value:5},{timestamp:next,value:4}]}
  ]),{labels:[t,t,next],datasets:[{label:'A',data:[1,9,null]},{label:'B',data:[5,null,4]}]});
});
