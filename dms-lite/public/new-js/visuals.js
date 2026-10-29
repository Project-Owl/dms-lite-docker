import {readPreferences,savePreferences,browserStorage} from './preferences.mjs';
import {fetchJson,showFailure,appendRow} from './api.mjs';
import {alignSeries} from './chart-data.mjs';
const storage = browserStorage();
let preferences = readPreferences(storage), chart, chartRequest=0;
const chartStatus = document.getElementById('chart-status');
const chartTopic = document.getElementById('chart-topic');
async function loadChart() {
  const request=++chartRequest, selectedPreferences={...preferences};
  try {
    const topics = await fetchJson('/api/topics');
    if(request!==chartRequest)return;
    chartTopic.replaceChildren();
    for (const topic of topics) chartTopic.add(new Option(topic,topic));
    if (!topics.length) {chartStatus.textContent='No numeric chart data yet. Waiting for device messages.';if(chart)chart.destroy();chart=null;return;}
    const topic = topics.includes(selectedPreferences.topic) ? selectedPreferences.topic : topics[0];
    chartTopic.value = topic;
    const selected = selectedPreferences.chartType === 'multiLine' && topics.includes(selectedPreferences.secondTopic) ? [topic,selectedPreferences.secondTopic] : [topic];
    const series = await Promise.all(selected.map(async label => ({label,...await fetchJson('/api/readings?'+new URLSearchParams({topic:label,limit:selectedPreferences.limit}))})));
    if(request!==chartRequest)return;
    const data = alignSeries(series);
    if (chart) chart.destroy();
    const colors = ['#80dac2','#e7b878'];
    data.datasets.forEach((dataset,i) => {dataset.borderColor=colors[i%colors.length];dataset.backgroundColor=colors[i%colors.length];dataset.spanGaps=false;});
    chart = new window.Chart(document.getElementById('mychart'),{type:selectedPreferences.chartType==='bar'?'bar':'line',data,options:{responsive:true,maintainAspectRatio:false,animation:false,plugins:{legend:{labels:{color:'#a2b3c2',boxWidth:12}}},scales:{x:{ticks:{color:'#a2b3c2',maxTicksLimit:5},grid:{color:'#2b3b49'}},y:{ticks:{color:'#a2b3c2'},grid:{color:'#2b3b49'}}}}});
    const count = series.reduce((sum,item)=>sum+item.samples.length,0);
    chartStatus.textContent = count ? `${count} numeric samples from recent messages.` : 'No numeric samples for this topic.';
  } catch {if(request===chartRequest)showFailure(chartStatus,loadChart);}
}
async function loadInfo() {
  const status = document.getElementById('info-status'), body = document.getElementById('info-body');body.replaceChildren();
  try {
    const ducks = await fetchJson('/api/ducks');
    const duck = ducks.includes(preferences.duckId) ? preferences.duckId : ducks[0];
    if (!duck) {status.textContent='No device messages yet.';return;}
    const {reading} = await fetchJson('/api/ducks/'+encodeURIComponent(duck)+'/latest');
    status.textContent=reading?'':'No message for this device.';
    if (reading) appendRow(body,[duck,reading.topic,reading.payload,reading.timestamp]);
  } catch {showFailure(status,loadInfo);}
}
async function loadAlerts() {
  const status = document.getElementById('alert-status'), body = document.getElementById('alert-body');body.replaceChildren();
  if (!preferences.alerts.length) {status.textContent='No alerts configured. Add thresholds in Settings.';return;}
  const results = await Promise.allSettled(preferences.alerts.map(async alert => {
    const {reading} = await fetchJson('/api/alerts?'+new URLSearchParams(alert));
    if (reading) appendRow(body,[reading.duckId,alert.topic,reading.value,reading.timestamp]);
  }));
  if (results.some(result=>result.status==='rejected')) showFailure(status,loadAlerts);
  else status.textContent=body.rows.length?'':'No outliers in recent messages.';
}
chartTopic?.addEventListener('change',() => {preferences=savePreferences(storage,{topic:chartTopic.value});loadChart();});
if(chartTopic)loadChart();
if(document.getElementById('info-body'))loadInfo();
if(document.getElementById('alert-body'))loadAlerts();
