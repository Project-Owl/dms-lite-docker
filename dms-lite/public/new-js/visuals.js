// -------- CHART Functionality --------------------
import * as Utils from './Utils.js';
// line chart configs
const data = {
  labels: null,
  datasets: [{
    label: 'data 1',
    data: null,
    borderColor: Utils.CHART_COLORS.red,
    tension: 0.1
  }
  ]
};
const configl = {
  type: 'line',
  data: data,
  options: {
    responsive: true,
    scales:{
      y:{
        beginAtZero: true
      }
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Chart.js Line Chart'
    }
  }
}
};
// multi axis line chart configs
const datam = {
  labels: null,
  datasets: [
    {
      label: 'Data 1',
      data: null,
      borderColor: Utils.CHART_COLORS.red,
      backgroundColor: Utils.CHART_COLORS.red,
      yAxisID: 'y',
    },
    {
      label: 'Data 1',
      data: null,
      borderColor: Utils.CHART_COLORS.red,
      backgroundColor: Utils.CHART_COLORS.red,
      yAxisID: 'y',
    }
  ]
};
const configm = {
  type: 'line',
  data: datam,
  options: {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    stacked: false,
    plugins: {
      title: {
        display: true,
        text: 'Chart.js Line Chart - Multi Axis'
      }
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',

        // grid line settings
        grid: {
          drawOnChartArea: false, // only want the grid lines for one axis to show up
        },
      },
    }
  },
};
//bar chart config
const datab = {
  labels: null,
  datasets: [{
    label: 'My First Dataset',
    data: null,
    borderColor: Utils.CHART_COLORS.red,
    backgroundColor: Utils.CHART_COLORS.red,
    borderWidth: 1
}]
};
const configb = {
  type: 'bar',
  data: datab,
  options: {
    scales: {
      y: {
        beginAtZero: true
      }
    }
  },
};
//make the tables
showAlerts();
showInfo();
//build chart
const mychart = document.getElementById("mychart");
var chart = new Chart(mychart, configl);
chart.data.datasets.pop();
chart.update();

const settings_json = localStorage.getItem("information"); 
const settings = JSON.parse(settings_json);
const typeOfGraph = settings[1]; 
const data_amount = settings[4]; 

if (typeOfGraph == "line"){getsingle();}
else if (typeOfGraph == "multiLine"){
  chart.destroy();
  chart = new Chart(mychart, configm);
  chart.data.datasets.pop();
  chart.data.datasets.pop();
  getMultiLine();
  chart.update();
}
else if (typeOfGraph == "bar"){
  chart.destroy();
  chart = new Chart(mychart, configb);
  chart.data.datasets.pop();
  getsingle();
  chart.update();
}
// const data_amount = localStorage.getItem("data_cutoff");
var element = document.getElementById("data_amount")
if (element){element.innerHTML = "Chart displays the top " + data_amount + " data points";
}
// ----------------CHARTING---------------------------------------------------------------------------------------------
async function getsingle() {
  const data_amount = settings[4]; 
  const topic = settings[2]; 
  
  const url = new URL('http://127.0.0.1:5000/showPayload/' + topic +'/'+ data_amount);
  // Storing response
  const response = await fetch(url);
  // Storing data in form of JSON 
  var payload = await response.json();
  const dsColor = Utils.namedColor(chart.data.datasets.length);
  const newDataset = {
        label: topic,
        borderColor: dsColor,
        backgroundColor: dsColor,
        data: payload["payload"]
      };
      const newlabels = payload["label"];
      chart.data.labels = newlabels;
      chart.data.datasets.push(newDataset);
      chart.update();
  }
async function getMultiLine (){
  const data_amount = settings[4]; 
  const topic = settings[2]; 
  const secondtopic = settings[3];
  const url = new URL('http://127.0.0.1:5000/showPayload/' + topic + '/'+ data_amount);
  const url2 = new URL('http://127.0.0.1:5000/showPayload/' + secondtopic + '/'+ data_amount)
  // Storing response
  const response = await fetch(url);
  const response2 = await fetch(url2);
  // Storing data in form of JSON
  const firstpayload = await response.json();
  const secondpayload = await response2.json();
  const data = [];
  const first_dataset = {
        label: topic,
        borderColor: Utils.CHART_COLORS.red,
        backgroundColor: Utils.CHART_COLORS.red,
        data: firstpayload["payload"]
      };
  data.push(first_dataset);
      // chart.data.datasets.push(newDataset);
  chart.options.plugins.title.text = 'Average ' + topic+ ' and ' + secondtopic+' over time';
  const second_dataset = {
    label: secondtopic,
    borderColor: Utils.CHART_COLORS.blue,
    backgroundColor: Utils.CHART_COLORS.blue,
    data: secondpayload["payload"] 
  };
  chart.data.datasets.push(first_dataset);
  chart.data.datasets.push(second_dataset);
  chart.data.labels = firstpayload["label"];
  chart.update();
}


// ----------------- ALERTS --------------------------------------------------------------------------
async function showAlerts(){
  const alerts = JSON.parse(localStorage.getItem("alert_information"));
  var topic, min, max; 
  const topic_name = Object.keys(alerts);  
  const alert_table = document.getElementById("alert_table"); 
  for (let i = 0; i< topic_name.length ; i++ ){
    // var fnl = {};
    topic = topic_name[i]; 
    min = alerts[topic][0]; 
    max = alerts[topic][1]; 
    const url = new URL('http://127.0.0.1:5000/checkAlert/'+ topic + '/' +min + '/' + max );
    var response = await fetch(url); 
    var sig_json = await response.json(); 
    for(var j = 0 ; j < 1; j++){
      let row = alert_table.insertRow(); 
      let cell = row.insertCell(); 
      cell.innerHTML = sig_json["duckid"][j];
      cell = row.insertCell(); 
      cell.innerHTML = topic; 
      cell = row.insertCell(); 
      cell.innerHTML = sig_json["payload"][j];
      cell = row.insertCell(); 
      cell.innerHTML = sig_json["label"][j];
    }

  // }
  // const alert_table = document.getElementById("alert_table"); 
  // console.log(total);
  // for(var i = 0; i<total.length;i++){
  //   var row = alert_table.insertRow(-1);
  //   const t = Object.keys(total[i]);
  //   let cell = row.insertCell(0); 
  //   cell.innerHTML = t; 
  //   var items = total[i];
  //   console.log(items)
  //   for(var j=0; j<3; j++){
  //     let cell_info = row.insertCell(0); 
  //     cell_info.innerHTML = items[ref[j]];
      
      // console.log(j)
    }
    

  }
   

async function showInfo(){
    const duck = JSON.parse(localStorage.getItem("information"));
    const url = new URL('http://127.0.0.1:5000/showData/'+ duck[0]); 
    const respond = await fetch(url); 
    const info = await respond.json(); 
    // const topic, payload, time; 
    const info_array = [duck[0], info["topic"], info["payload"],info["timestamp"]]; 
    const info_table = document.getElementById("info_table"); 
    let row = info_table.insertRow(); 
    info_array.forEach(items => {
      let cell = row.insertCell(-1); 
      cell.innerHTML = items; 
    });
    }
     


