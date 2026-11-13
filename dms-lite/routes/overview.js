// Snapshot presentation only: no writes, connection probes, or device commands.
function deviceState(timestamp,staleAfterSeconds,now=Date.now()) {
  const time=typeof timestamp==='string'?Date.parse(timestamp):NaN;
  const age=(now-time)/1000;
  if(!Number.isFinite(age))return {recent:false,ageText:'Timestamp unavailable'};
  if(age<0)return {recent:false,ageText:'Timestamp ahead of host clock'};
  const seconds=Math.floor(age),minutes=Math.floor(age/60),hours=Math.floor(age/3600),days=Math.floor(age/86400);
  const [amount,unit]=seconds<60?[seconds,'second']:minutes<60?[minutes,'minute']:hours<24?[hours,'hour']:[days,'day'];
  return {recent:age<=staleAfterSeconds,ageText:`${amount} ${unit}${amount===1?'':'s'} ago`};
}
function formatUtc(timestamp) {
  const date=new Date(timestamp);
  return timestamp&&Number.isFinite(date.getTime())?date.toISOString().replace('T',' ').replace('.000Z',' UTC'):'Timestamp unavailable';
}
async function loadOverview(db,staleAfterSeconds,now=Date.now()) {
  const results=await Promise.allSettled([
    Promise.resolve().then(()=>db.getAllData()),Promise.resolve().then(()=>db.getDuckPlusData()),Promise.resolve().then(()=>db.getTopics())
  ]);
  const keys=['messages','devices','topics'];const snapshot={errors:{},snapshotAt:new Date(now).toISOString()};
  results.forEach((result,i)=>{snapshot[keys[i]]=result.status==='fulfilled'?result.value:[];snapshot.errors[keys[i]]=result.status!=='fulfilled';});
  snapshot.loadedCount=snapshot.errors.messages?null:snapshot.messages.length;
  snapshot.deviceCount=snapshot.errors.devices?null:snapshot.devices.length;
  snapshot.recentCount=snapshot.errors.devices?null:snapshot.devices.filter(row=>deviceState(row.timestamp,staleAfterSeconds,now).recent).length;
  snapshot.topicCount=snapshot.errors.topics?null:snapshot.topics.length;
  snapshot.latest=[...snapshot.messages,...snapshot.devices].map(row=>row.timestamp).filter(time=>typeof time==='string'&&Number.isFinite(Date.parse(time))&&Date.parse(time)<=now).sort((a,b)=>Date.parse(b)-Date.parse(a))[0]||null;
  snapshot.isEmpty=snapshot.loadedCount===0&&snapshot.deviceCount===0;
  return snapshot;
}
module.exports={loadOverview,deviceState,formatUtc};
