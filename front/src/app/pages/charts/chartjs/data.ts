import { ChartType } from './chartjs.model';

/**
 * Line Area Chart
 */
 const lineAreaChart: ChartType = {
  labels: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October"],
  datasets: [
    {
        label: "Sales Analytics",
        fill: true,
        lineTension: 0.5,
        backgroundColor: "rgba(64,81,137, 0.2)",
        borderColor: "#405189",
        borderCapStyle: 'butt',
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: 'miter',
        pointBorderColor: "#405189",
        pointBackgroundColor: "#fff",
        pointBorderWidth: 1,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#405189",
        pointHoverBorderColor: "#fff",
        pointHoverBorderWidth: 2,
        pointRadius: 1,
        pointHitRadius: 10,
        data: [65, 59, 80, 81, 56, 55, 40, 55, 30, 80]
    },
    {
        label: "Monthly Earnings",
        fill: true,
        lineTension: 0.5,
        backgroundColor: "rgba(10,179,156, 0.2)",
        borderColor: "#0ab39c",
        borderCapStyle: 'butt',
        borderDash: [],
        borderDashOffset: 0.0,
        borderJoinStyle: 'miter',
        pointBorderColor: "#0ab39c",
        pointBackgroundColor: "#fff",
        pointBorderWidth: 1,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#0ab39c",
        pointHoverBorderColor: "#eef0f2",
        pointHoverBorderWidth: 2,
        pointRadius: 1,
        pointHitRadius: 10,
        data: [80, 23, 56, 65, 23, 35, 85, 25, 92, 36]
    }
  ],
  options: {
      defaultFontColor: '#8791af',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
          xAxes: [
              {
                  gridLines: {
                      color: 'rgba(166, 176, 207, 0.1)',
                  },
              },
          ],
          yAxes: [
              {
                  ticks: {
                      max: 100,
                      min: 20,
                      stepSize: 10,
                  },
                  gridLines: {
                      color: 'rgba(166, 176, 207, 0.1)',
                  },
              },
          ],
      },

  }
};

/**
 * Line Bar Chart
 */
 const lineBarChart: ChartType = {
  labels: ["January", "February", "March", "April", "May", "June", "July"],
  datasets: [
      {
          label: "Sales Analytics",
          backgroundColor: "rgba(64,81,137, 0.8)",
          borderColor: "rgba(64,81,137, 0.8)",
          borderWidth: 1,
          hoverBackgroundColor: "rgba(64,81,137, 0.9)",
          hoverBorderColor: "rgba(64,81,137, 0.9)",
          data: [65, 59, 81, 45, 56, 80, 50,20]
      }
  ],
  options: {
      maintainAspectRatio: false,
      scales: {
          xAxes: [
              {
                  gridLines: {
                      color: 'rgba(166, 176, 207, 0.1)'
                  },
              }
          ],
          yAxes: [
              {
                  gridLines: {
                      color: 'rgba(166, 176, 207, 0.1)'
                  }
              }
          ]
      }
  }
};

/**
 * Pie Chart
 */
 const pieChart: ChartType = {
  labels: [
    "Desktops",
    "Tablets"
        ],
  datasets: [
  {
      data: [300, 180],
      backgroundColor: ["#0ab39c","#f3f6f9"],
      hoverBackgroundColor: ["#0ab39c","#f3f6f9"],
      hoverBorderColor: "#fff"
  }],
  options: {
      maintainAspectRatio: false,
      legend: {
          position: 'top',
      }
  }
};

/**
 * Donut Chart
 */
 const donutChart: ChartType = {
  labels: [
    "Desktops",
    "Tablets"
  ],
  datasets: [
    {
        data: [300, 210],
        backgroundColor: ["#405189","#f3f6f9"],
        hoverBackgroundColor: ["#405189","#f3f6f9"],
        hoverBorderColor: "#fff"
    }],
  options: {
      maintainAspectRatio: false,
      legend: {
          position: 'top',
      }
  }
};

/**
 * Polar Chart
 */
 const polarChart: ChartType = {
  labels: [
    "Series 1",
    "Series 2",
    "Series 3",
    "Series 4"
  ],
  datasets: [{
      data: [
          11,
          16,
          7,
          18
      ],
      backgroundColor: ["#f06548", "#0ab39c", "#f7b84b", "#405189"],
      label: 'My dataset', // for legend
      hoverBorderColor: "#fff"
  }],
  options: {
      maintainAspectRatio: false,
      legend: {
          position: 'top',
      }
  }
};

/**
 * Redar Chart
 */
 const radarChart: ChartType = {
  labels: ["Eating", "Drinking", "Sleeping", "Designing", "Coding", "Cycling", "Running"],
  datasets: [
      {
          label: "Desktops",
          backgroundColor: "rgba(42, 181, 125, 0.2)",
          borderColor: "#2ab57d", //"#2ab57d",
          pointBackgroundColor: "#2ab57d", //"#2ab57d",
          pointBorderColor: "#fff",
          pointHoverBackgroundColor: "#fff",
          pointHoverBorderColor: "#2ab57d", //"#2ab57d",
          data: [65, 59, 90, 81, 56, 55, 40]
      },
      {
          label: "Tablets",
          backgroundColor: "rgba(81, 86, 190, 0.2)", //"rgba(81, 86, 190, 0.2)",
          borderColor: "#5156be", //"#5156be",
          pointBackgroundColor: "#5156be", //"#5156be",
          pointBorderColor: "#fff",
          pointHoverBackgroundColor: "#fff",
          pointHoverBorderColor: "#5156be", //"#5156be",
          data: [28, 48, 40, 19, 96, 27, 100]
      }
  ],
  options: {
      maintainAspectRatio: false,
      legend: {
          position: 'top'
      }
  }
};


export { lineAreaChart, lineBarChart, pieChart, donutChart, polarChart, radarChart};
