// Filter the loaded snapshot only; packet text is never interpreted as markup.
const search=document.getElementById('message-search');
const topic=document.getElementById('message-topic');
if(search&&topic){
  const rows=[...document.querySelectorAll('.message-row')];
  for(const value of [...new Set(rows.map(row=>row.dataset.topic))].sort())topic.add(new Option(value,value));
  const apply=()=>{
    const query=search.value.trim().toLowerCase();let count=0;
    for(const row of rows){const match=(!topic.value||row.dataset.topic===topic.value)&&row.textContent.toLowerCase().includes(query);row.hidden=!match;if(match)count++;}
    document.getElementById('message-filter-status').textContent=`Showing ${count} of ${rows.length} loaded messages`;
  };
  search.addEventListener('input',apply);topic.addEventListener('change',apply);
}
