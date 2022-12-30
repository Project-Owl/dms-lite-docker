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

//build chart
const mychart = document.getElementById("mychart");
var chart = new Chart(mychart, configl);
chart.data.datasets.pop();
chart.update();
const typeOfGraph = localStorage.getItem("typeGraph")
if (typeOfGraph == "line"){
  getsingle();
}
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
const data_amount = localStorage.getItem("data_cutoff");
var element = document.getElementById("data_amount")
if (element){
  element.innerHTML = "Data displays the top " + data_amount + " data points";

}

// ----------------BUTTONS AND INPUTS---------------------------------------------------------------------------------------------
function getsingle (){
  const topic = localStorage.getItem("topicDisplay");
  const data_cutoff = localStorage.getItem("data_cutoff")
  const url = new URL('http://127.0.0.1:5000/showPayload/' + topic +'/'+ data_cutoff);
  let xhr = new XMLHttpRequest();
  xhr.open('GET', url);
  xhr.responseType = 'json';
  xhr.send();
  xhr.onload = function(){
    let responseObj = xhr.response;
    const resultPayload = responseObj;
    console.log(resultPayload);
    const dsColor = Utils.namedColor(chart.data.datasets.length);
    const newDataset = {
      label: topic,
      borderColor: dsColor,
      backgroundColor: dsColor,
      data: resultPayload["payload"]
    };
    
    const newlabels = resultPayload["label"]
    chart.data.labels = newlabels;
    chart.data.datasets.push(newDataset);

    chart.update();
  }
}

function getMultiLine (){
  const topic = localStorage.getItem("topicDisplay");
  const data_cutoff = localStorage.getItem("data_cutoff");
  const url = new URL('http://127.0.0.1:5000/showPayload/' + topic + '/'+ data_cutoff);
  let xhr = new XMLHttpRequest();
  xhr.open('GET', url);
  xhr.responseType = 'json';
  xhr.send();
  xhr.onload = function(){
    let responseObj = xhr.response;
    const resultPayload = responseObj;
    const dsColor = Utils.namedColor(chart.data.datasets.length);
    const newDataset = {
      label: topic,
      borderColor: dsColor,
      data: resultPayload["payload"]
     };
    
    const newlabels = resultPayload["label"]
    chart.data.labels = newlabels;
    chart.data.datasets.push(newDataset);
    chart.options.plugins.title.text = 'Average ' + topic + ' over time';
    chart.update();
  }
  const secondtopic = localStorage.getItem("topicDisplay2");
  const urlsecondcall = new URL('http://127.0.0.1:5000/showPayload/' + secondtopic + '/'+data_cutoff)
  let xhrv2 = new XMLHttpRequest();
  xhrv2.open('GET', urlsecondcall);
  xhrv2.responseType = 'json';
  xhrv2.send();
  xhrv2.onload = function(){
    let responseOb = xhrv2.response;
    const resultPayload = responseOb;
    
    const dsColor = Utils.namedColor(chart.data.datasets.length);
    const newDataset = {
      label: secondtopic,
      borderColor: dsColor,
      data: resultPayload["payload"]
     };

    
    const newlabels = resultPayload["label"]
    chart.data.labels = newlabels;
    console.log(chart.data.datasets)
    chart.data.datasets.push(newDataset);
    chart.options.plugins.title.text = 'Average ' + secondtopic + ' over time';
    chart.update();
  }
}
// ----------------------------------------------------------------------------

//warning messsage for max/min data from settings
// will be updated to just send once
// getAlert()
// function getAlert(){
//   if (localStorage.getItem("topicWarning")){
//     const topicAlert = localStorage.getItem("topicWarning");
//     const topicMax = localStorage.getItem("TopicWarningMax")
//   const outlier_url = new URL('http://127.0.0.1:5000/checkOutlier/' + topicAlert + '/' + topicMax + '/0')
//   let outlierxhr = new XMLHttpRequest();
//   outlierxhr.open('GET', outlier_url);
//   outlierxhr.responseType = 'json';
//   outlierxhr.send();
//   outlierxhr.onload = function(){
//     let responseObj = outlierxhr.response;
//     const outdic = responseObj;
//     alert("Topic:"+ topicAlert+" has exceeded:"+topicMax+"at \n" + outdic["label"] + "\n with: " + outdic["payload"]+"\n") 
//   }
//   }
// }

//-----------------------------------------------------------------------------
//testing  out refresh rate (need to fix settings problem first)
// function autoRefresh() {
//   window.location = window.location.href;
//   console.log('5min have passed')
// }
// setInterval(autoRefresh, 30000);
// ---------------------------------------------------------------------------------

