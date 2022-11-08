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
    var sele = document.getElementById("selecttopic");
    console.log(sele);
    var selectvalue = document.getElementsByClassName("selecttopic");
    console.log(selectvalue)
    for(var j = 0; j < selectvalue.length; j++){
      console.log(selectvalue[j])
      var selection = selectvalue[j]
    for(var i = 0; i < topicdic["topics"].length; i++){
      var selected = document.createElement("OPTION");
      var text = document.createTextNode(topicdic["topics"][i]);
      selected.appendChild(text);
      selected.setAttribute("value", topicdic["topics"][i]);
      selection.insertBefore(selected,selection.lastChild);
    }
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
    const data = document.getElementById('datamount').value
    const typegraph = typegraphselect.options[typegraphselect.selectedIndex].value
    localStorage.setItem("typeGraph", typegraph);
    localStorage.setItem("data_cutoff", data);
    // if 1 topic
    if (typegraph == "line" || typegraph == "bar") {
    var select = document.getElementById('firsttopic');
    const topic = select.options[select.selectedIndex].value;
    localStorage.setItem("topicDisplay", topic);
    }
    //if 2 topic
    else if (typegraph == "multiLine"){
      var select = document.getElementById('firsttopic');
      var select2 = document.getElementById('secondtopic');
      const topic = select.options[select.selectedIndex].value;
      const topic2 = select2.options[select2.selectedIndex].value;
      localStorage.setItem("topicDisplay",topic);
      localStorage.setItem("topicDisplay2",topic2);
    }
  }