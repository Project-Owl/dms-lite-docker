const http=require('node:http');
const {createApp}=require('../app');
let populated=true,unavailable=false;
const raw='<img src=x onerror="window.PACKET_EXECUTED=true">';
const packet={timestamp:new Date(Date.now()-8000).toISOString(),duck_id:'D1',topic:'sensor/temp',message_id:'M1',payload:raw,path:'A,B',hops:2,duck_type:1};
const db={checkReady:async()=>{}, getAllData:async()=>{if(unavailable)throw Error('private fixture failure');return populated?[packet,{...packet,topic:'gps',payload:'x,y,NaN,200'}]:[];},getDuckPlusData:async()=>populated?[packet]:[],getTopics:async()=>populated?['sensor/temp','humidity']:[],getUniqueDucks:async()=>populated?[{duck_id:'D1'}]:[],getReadings:async()=>({samples:populated?[{timestamp:new Date(Date.now()-8000).toISOString(),value:2.5}]:[]}),getAlert:async()=>({reading:populated?{timestamp:packet.timestamp,duckId:raw,value:2.5}:null}),getLatestByDuckId:async()=>({reading:populated?{timestamp:packet.timestamp,topic:packet.topic,payload:raw}:null})};
db.postCommand=async()=>{};
const app=createApp({db}),serialApp=createApp({db,commandsEnabled:true});
const server=http.createServer((req,res)=>{
  if(req.url.startsWith('/__fixture')){populated=!req.url.includes('empty');unavailable=req.url.includes('unavailable');packet.duck_id=req.url.includes('long')?'DUCK-'+('X'.repeat(240))+raw:'D1';res.end('ok');return;}
  app(req,res);
});
server.listen(Number(process.env.TEST_PORT||3107),'127.0.0.1');

http.createServer(serialApp).listen(3108,'127.0.0.1');
