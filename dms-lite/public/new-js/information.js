import {readPreferences,savePreferences,browserStorage} from './preferences.mjs';
import {fetchJson,showFailure,appendRow} from './api.mjs';
const storage = browserStorage();
let preferences = readPreferences(storage);
const status = document.getElementById('settings-status');
function display() {
  document.getElementById('graphtype').value = preferences.chartType;
  document.getElementById('datamount').value = preferences.limit;
  const alerts=document.getElementById('saved-alerts');alerts.replaceChildren();
  for(const alert of preferences.alerts){const item=document.createElement('li');item.textContent=`${alert.topic}: below ${alert.min} or above ${alert.max}`;alerts.append(item);}
  if(!preferences.alerts.length){const item=document.createElement('li');item.textContent='No alert thresholds configured.';alerts.append(item);}
  const body = document.getElementById('table_body'); body.replaceChildren();
  appendRow(body,[preferences.duckId || 'Not selected',preferences.chartType,preferences.topic || 'Not selected',preferences.secondTopic,preferences.limit]);
}
const optionStatus=document.getElementById('settings-options-status');
let topicsReady=false,ducksReady=false,loadingOptions=false;
function populate(select,values,saved='') {
  select.replaceChildren();
  for(const value of values)select.add(new Option(value,value));
  if(saved&&!values.includes(saved))select.add(new Option(saved+' (saved)',saved));
  if(saved)select.value=saved;
  select.disabled=!select.options.length;
}
for(const [id,value] of [['firsttopic',preferences.topic],['secondtopic',preferences.secondTopic],['selectduck',preferences.duckId],['topic_alert','']]){
  const select=document.getElementById(id);select.add(new Option(value||'Loading options…',value));select.disabled=true;
}
document.getElementById('alert_bt').disabled=true;
async function loadOptions() {
  if(loadingOptions)return;
  loadingOptions=true;optionStatus.textContent='Loading topics and devices…';
  const results=await Promise.allSettled([
    topicsReady?Promise.resolve():fetchJson('/api/topics').then(topics=>{
      populate(document.getElementById('firsttopic'),topics,preferences.topic);
      populate(document.getElementById('secondtopic'),topics,preferences.secondTopic);
      populate(document.getElementById('topic_alert'),topics);
      topicsReady=true;document.getElementById('alert_bt').disabled=!topics.length;
    }),
    ducksReady?Promise.resolve():fetchJson('/api/ducks').then(ducks=>{
      populate(document.getElementById('selectduck'),ducks,preferences.duckId);ducksReady=true;
    })
  ]);
  loadingOptions=false;
  if(results.some(result=>result.status==='rejected'))showFailure(optionStatus,loadOptions);
  else optionStatus.textContent=document.getElementById('topic_alert').options.length?'':'No messages yet. Options appear after data arrives.';
}
function save(changes) {
  preferences = savePreferences(storage,changes); display(); status.textContent = 'Saved settings for this browser.';
}
document.getElementById('toData').addEventListener('click',() => {
  const limit = Number(document.getElementById('datamount').value);
  if (!Number.isInteger(limit) || limit < 1 || limit > 1000) {status.textContent = 'Choose a data limit from 1 to 1000.';return;}
  const changes={chartType:document.getElementById('graphtype').value,limit};
  if(topicsReady)Object.assign(changes,{topic:document.getElementById('firsttopic').value,secondTopic:document.getElementById('secondtopic').value});
  if(ducksReady)changes.duckId=document.getElementById('selectduck').value;
  save(changes);
});
document.getElementById('alert_bt').addEventListener('click',() => {
  const topic = document.getElementById('topic_alert').value;
  const low = document.getElementById('min_alert').value, high = document.getElementById('max_alert').value;
  const min = Number(low), max = Number(high);
  if (!topic || !low.trim() || !high.trim() || !Number.isFinite(min) || !Number.isFinite(max) || min > max) {
    status.textContent = 'Choose a topic and valid minimum/maximum values.';return;
  }
  save({alerts:[...preferences.alerts.filter(alert=>alert.topic!==topic),{topic,min,max}]});
});
document.getElementById('detailedView').addEventListener('change',event => {
  document.cookie = 'detailedView='+event.target.checked+'; Path=/; SameSite=Lax';
});
display();loadOptions();
