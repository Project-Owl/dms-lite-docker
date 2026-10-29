export function alignSeries(series) {
  const timestamps = [...new Set(series.flatMap(item => item.samples.map(sample => sample.timestamp)))].sort();
  const buckets = series.map(item => {
    const values = new Map();
    for (const sample of item.samples) {
      if (!values.has(sample.timestamp)) values.set(sample.timestamp,[]);
      values.get(sample.timestamp).push(sample.value);
    }
    return values;
  });
  // Whole-second device timestamps can contain bursts: give each occurrence a slot.
  const slots = timestamps.flatMap(timestamp => Array.from({length:Math.max(...buckets.map(values => values.get(timestamp)?.length || 0))},(_,index) => ({timestamp,index})));
  return {labels:slots.map(slot => slot.timestamp),datasets:series.map((item,i) => ({
    label:item.label,data:slots.map(({timestamp,index}) => buckets[i].get(timestamp)?.[index] ?? null)
  }))};
}
