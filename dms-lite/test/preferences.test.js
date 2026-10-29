const {test}=require('node:test');
const assert=require('node:assert/strict');
const memory=(initial={})=>{const values=new Map(Object.entries(initial));return {getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v)};};
test('fresh, malformed and inaccessible storage recover to safe preferences',async()=>{
  const {readPreferences}=await import('../public/new-js/preferences.mjs');
  for(const store of [memory(),memory({'dmsLite.preferences':'{'}),{getItem(){throw new Error('denied');}}]) {
    const pref=readPreferences(store); assert.equal(pref.limit,100);assert.deepEqual(pref.alerts,[]);assert.equal(pref.chartType,'line');
  }
});
test('legacy migration preserves unrelated entries and supports prototype-like topic names',async()=>{
  const {readPreferences,savePreferences}=await import('../public/new-js/preferences.mjs');
  const store=memory({other:'keep',information:'["D1","multiLine","temp","humidity",12]',alert_information:'{"__proto__":[-2.5,10]}'});
  assert.deepEqual(readPreferences(store),{version:1,duckId:'D1',chartType:'multiLine',topic:'temp',secondTopic:'humidity',limit:12,alerts:[{topic:'__proto__',min:-2.5,max:10}]});
  const saved=savePreferences(store,{limit:1000});assert.equal(saved.limit,1000);assert.equal(store.getItem('other'),'keep');
  assert.equal(readPreferences(store).limit,1000);
  assert.equal(savePreferences(store,{limit:0,alerts:[{topic:'temp',min:10,max:1}]}).limit,100);
  assert.equal(readPreferences(store).alerts.length,0);
  assert.equal(savePreferences(store,{limit:1}).limit,1);
});
test('saving preferences tolerates browser quota/security failures',async()=>{
  const {savePreferences}=await import('../public/new-js/preferences.mjs');
  const pref=savePreferences({getItem:()=>null,setItem:()=>{throw new Error('full');}},{topic:'temp'});
  assert.equal(pref.topic,'temp');
});
