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
      label: 'Data 2',
      data: null,
      borderColor: Utils.CHART_COLORS.blue,
      backgroundColor: Utils.CHART_COLORS.blue,
      yAxisID: 'y1',
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


//build chart
const mychart = document.getElementById("mychart");
var chart = new Chart(mychart, configl);
chart.data.datasets.pop();
chart.update();
const typeOfGraph = localStorage.getItem("typeGraph")
if (typeOfGraph == "line"){
  getline();
}
// else if (typeOfGraph == "multiLine"){
//   chart.destroy();
//   chart = new Chart(mychart, configm);


// }
// ----------------BUTTONS AND INPUTS---------------------------------------------------------------------------------------------
  //get();
function getline (){
  const topic = localStorage.getItem("topicDisplay");
  const url = new URL('http://127.0.0.1:5000/showPayload/' + topic)
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
// testing  out refresh rate (need to fix settings problem first)
// function autoRefresh() {
//   window.location = window.location.href;
//   console.log('5min have passed')
// }
// setInterval(autoRefresh, 300000);
// ---------------------------------------------------------------------------------

