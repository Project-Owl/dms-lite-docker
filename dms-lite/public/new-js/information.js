//settings script
// call the topics from the DB

const topicurl = new URL('http://127.0.0.1:5000/getTopics')
const duckurl = new URL('http://127.0.0.1:5000/getDucks')
// ----------------------------------------------------------------------------------------------
// Try using the Fetch() API instead 
// Defining async function

async function getapi(url_t, url_d) {
    
  // Storing response
  const response = await fetch(url_t);
  // Storing data in form of JSON
  var topics = await response.json();
  var selectvalue = document.getElementsByClassName("selecttopic");
  for(var j = 0; j < selectvalue.length; j++){
    var selection = selectvalue[j]
  for(var i = 0; i < topics.length; i++){
    var selected = document.createElement("OPTION");
    var text = document.createTextNode(topics[i]);
    selected.appendChild(text);
    selected.setAttribute("value", topics[i]);
    selection.insertBefore(selected,selection.lastChild);
  }
}
////////////////////////////////////////////////////////////////
  const resp_ducks = await fetch(url_d); 
  var ducks = await resp_ducks.json(); 
  var select_duck = document.getElementsByClassName("selectduck");
  for(var j = 0; j < select_duck.length; j++){
    var sel = select_duck[j]
  for(var i = 0; i < ducks.length; i++){
    var s = document.createElement("OPTION");
    var text = document.createTextNode(ducks[i]);
    s.appendChild(text);
    s.setAttribute("value", ducks[i]);
    sel.insertBefore(s,sel.lastChild);


  }
}
}
// Calling that async function
getapi(topicurl, duckurl);
  
///---------------------------------------------------------------------------------------------
  // sets data for the graph in Data
  document.getElementById('toData').addEventListener("click", store);
  function store(){
    // Local Storage and Charting variables
    var local = [];
    const duck_s = document.getElementById('selectduck'); 
    const duck = duck_s.options[duck_s.selectedIndex].value;
    local.push(duck)

    var typegraphselect = document.getElementById('graphtype');
    const data = document.getElementById('datamount').value
    const typegraph = typegraphselect.options[typegraphselect.selectedIndex].value
    local.push(typegraph); 

    var select = document.getElementById('firsttopic');
    const topic = select.options[select.selectedIndex].value;
    local.push(topic);
    
    //if 2 topic
    if (typegraph == "multiLine"){
      var select2 = document.getElementById('secondtopic');
      const topic2 = select2.options[select2.selectedIndex].value;
      local.push(topic2);
    }
    else{local.push("")}
    local.push(data);
    localStorage.setItem("information", JSON.stringify(local))

    // Local storage and Alert variables 
  }
  document.getElementById('alert_bt').addEventListener("click", alert);
  function alert(){
    //var alert_sys={}; 
    var topic_alert_id = document.getElementById('topic_alert'); 
    const topic_alert = topic_alert_id.options[topic_alert_id.selectedIndex].value;
    var min_alert = document.getElementById('min_alert').value;
    var max_alert = document.getElementById('max_alert').value; 
     
    var prevent_overwrite = JSON.parse(localStorage.getItem("alert_information"));
    prevent_overwrite[topic_alert] = [min_alert,max_alert];
    localStorage.setItem("alert_information", JSON.stringify(prevent_overwrite));
  }

  //-------------------------------------------------------------------------------------
  //Populate the table 
function loadTableData(){
  const array_val = [];
  $.each(localStorage, function(key, value){array_val.push(value);});
  const table = document.getElementById("table_body");
  const setting = JSON.parse(array_val[0]); 
  let row = table.insertRow(); 
  setting.forEach(item => {
    let cell = row.insertCell(-1); 
    cell.innerHTML = item;
  })
} 
loadTableData();