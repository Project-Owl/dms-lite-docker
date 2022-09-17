//settings script
// call the topics from the DB
const topicurl = new URL('http://127.0.0.1:5000/getTopics')
let topxhr = new XMLHttpRequest();
  topxhr.open('GET', topicurl);
  topxhr.responseType = 'json';
  topxhr.send();
  topxhr.onload = function(){
    let responseObj = topxhr.response;
    const topicdic = responseObj;
    var selectvalue = document.getElementById("selecttopic");
    for(var i = 0; i < topicdic["topics"].length; i++){
      var selected = document.createElement("OPTION");
      var text = document.createTextNode(topicdic["topics"][i]);
      selected.appendChild(text);
      selected.setAttribute("value", topicdic["topics"][i]);
      selectvalue.insertBefore(selected,selectvalue.lastChild);
      }
  }
///---------------------------------------------------------------------------------------------
  //Alert options
// let alertxhr = new XMLHttpRequest();
// alertxhr.open('GET', topicurl);
// alertxhr.responseType = 'json';
//   alertxhr.send();
//   alertxhr.onload = function(){
//     let AlertresponseObj = alertxhr.response;
//     const Alerttopicdic = AlertresponseObj;
//     var Aselectvalue = document.getElementById("selecttopicWarning");
//     for(var i = 0; i < Alerttopicdic["topics"].length; i++){
//       var selected = document.createElement("OPTION");
//       var text = document.createTextNode(Alerttopicdic["topics"][i]);
//       selected.appendChild(text);
//       selected.setAttribute("value", Alerttopicdic["topics"][i]);
//       Aselectvalue.insertBefore(selected,Aselectvalue.lastChild);
//       }
//   }

  //------------------------------------------------------------------------
  //button in settings === final sent to the server
  
  // sets data for the graph in Data
  document.getElementById('toData').addEventListener("click", store)
  function store(){
    var typegraphselect = document.getElementById('graphtype');
    const typegraph = typegraphselect.options[typegraphselect.selectedIndex].value
    console.log(typegraph)
    if (typegraph == "line"){
    var select = document.getElementById('selecttopic');
    const topic = select.options[select.selectedIndex].value;
    localStorage.setItem("typeGraph", typegraph);
    localStorage.setItem("topicDisplay", topic);
    }
    else if (typegraph == "multiLine"){
      localStorage.setItem("typeGraph", typegraph);
    }
  }