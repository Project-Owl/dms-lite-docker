const KEY = 'dmsLite.preferences';
const text = value => typeof value === 'string' && value.length <= 1024 ? value : '';
function normalize(value = {}) {
  if (!value || typeof value !== 'object') value = {};
  const limit = Number(value.limit);
  return {version:1, chartType:['line','bar','multiLine'].includes(value.chartType) ? value.chartType : 'line',
    topic:text(value.topic), secondTopic:text(value.secondTopic),
    limit:Number.isInteger(limit) && limit >= 1 && limit <= 1000 ? limit : 100,
    duckId:text(value.duckId), alerts:Array.isArray(value.alerts) ? value.alerts.filter(alert =>
      alert && text(alert.topic).trim() && typeof alert.min === 'number' && typeof alert.max === 'number' &&
      Number.isFinite(alert.min) && Number.isFinite(alert.max) && alert.min <= alert.max)
      .map(({topic,min,max}) => ({topic,min,max})) : []};
}
export function readPreferences(storage) {
  try {
    const stored = storage.getItem(KEY);
    if (stored !== null) {
      const value = JSON.parse(stored);
      return normalize(value?.version === 1 ? value : {});
    }
    const legacy = JSON.parse(storage.getItem('information') || 'null');
    const alerts = JSON.parse(storage.getItem('alert_information') || '{}');
    const value = Array.isArray(legacy) ? {duckId:legacy[0],chartType:legacy[1],topic:legacy[2],secondTopic:legacy[3],limit:legacy[4]} : {};
    value.alerts = alerts && typeof alerts === 'object' ? Object.entries(alerts).filter(([,bounds]) =>
      Array.isArray(bounds) && bounds.length === 2 && bounds.every(v => v !== '' && v !== null && Number.isFinite(Number(v))))
      .map(([topic,bounds]) => ({topic,min:Number(bounds[0]),max:Number(bounds[1])})) : [];
    const pref = normalize(value);
    try {storage.setItem(KEY,JSON.stringify(pref));} catch {}
    return pref;
  } catch {return normalize();}
}
export function savePreferences(storage,changes) {
  const pref = normalize({...readPreferences(storage),...changes});
  try {storage.setItem(KEY,JSON.stringify(pref));} catch {}
  return pref;
}
export function browserStorage() {
  try {return window.localStorage;} catch {return {getItem:()=>null,setItem:()=>{}};}
}
