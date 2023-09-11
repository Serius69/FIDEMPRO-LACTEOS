import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-chartjs',
  templateUrl: './chartjs.component.html',
  styleUrls: ['./chartjs.component.scss']
})
/**
 * Chartjs Component
 */
export class ChartjsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  // Line Chart
  lineAreaChart!: any;
  // Line Bar Chart
  lineBarChart!: any;
  // Pie Chart
  pieChart!: any;
  // Donut Chart
  donutChart!: any;
  // Polar Chart
  polarChart!: any;
  // Radar Chart
  radarChart!: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Charts' },
      { label: 'Chartjs', active: true }
    ];

    // Chart Color Data Get Function
    this._lineAreaChart('["--vz-primary-rgb, 0.2", "--vz-primary", "--vz-success-rgb, 0.2", "--vz-success"]');
    this._lineBarChart('["--vz-primary-rgb, 0.8", "--vz-primary-rgb, 0.9"]');
    this._pieChart('["--vz-success", "--vz-light"]');
    this._donutChart('["--vz-primary", "--vz-light"]');
    this._polarChart('["--vz-danger", "--vz-success", "--vz-warning", "--vz-primary"]');
    this._radarChart('["--vz-success-rgb, 0.2", "--vz-success", "--vz-primary-rgb, 0.2", "--vz-primary"]');
  }

  // Chart Colors Set
  private getChartColorsArray(colors:any) {
    colors = JSON.parse(colors);
    return colors.map(function (value:any) {
      var newValue = value.replace(" ", "");
      if (newValue.indexOf(",") === -1) {
        var color = getComputedStyle(document.documentElement).getPropertyValue(newValue);
            if (color) {
            color = color.replace(" ", "");
            return color;
            }
            else return newValue;;
        } else {
            var val = value.split(',');
            if (val.length == 2) {
                var rgbaColor = getComputedStyle(document.documentElement).getPropertyValue(val[0]);
                rgbaColor = "rgba(" + rgbaColor + "," + val[1] + ")";
                return rgbaColor;
            } else {
                return newValue;
            }
        }
    });
  }

  /**
 * Line Area Chart
 */
  private _lineAreaChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.lineAreaChart = {
      labels: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October"],
      datasets: [
        {
            label: "Sales Analytics",
            fill: true,
            lineTension: 0.5,
            backgroundColor: colors[0],
            borderColor: colors[1],
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: colors[1],
            pointBackgroundColor: "#fff",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: colors[1],
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
            backgroundColor: colors[2],
            borderColor: colors[3],
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: colors[3],
            pointBackgroundColor: "#fff",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: colors[3],
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
    }
  }

  /**
 * Line Bar Chart
 */
  private _lineBarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.lineBarChart = {
      labels: ["January", "February", "March", "April", "May", "June", "July"],
      datasets: [
          {
              label: "Sales Analytics",
              backgroundColor: colors[0],
              borderColor: colors[0],
              borderWidth: 1,
              hoverBackgroundColor: colors[1],
              hoverBorderColor: colors[1],
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
  }
  
 /**
 * Pie Chart
 */
  private _pieChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.pieChart = {
      labels: [
        "Desktops",
        "Tablets"
            ],
      datasets: [
      {
          data: [300, 180],
          backgroundColor: colors,
          hoverBackgroundColor: colors,
          hoverBorderColor: "#fff"
      }],
      options: {
          maintainAspectRatio: false,
          legend: {
              position: 'top',
          }
      }
    };
  }

  /**
 * Donut Chart
 */
  private _donutChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.donutChart = {
      labels: [
        "Desktops",
        "Tablets"
      ],
      datasets: [
        {
            data: [300, 210],
            backgroundColor: colors,
            hoverBackgroundColor: colors,
            hoverBorderColor: "#fff"
        }],
      options: {
          maintainAspectRatio: false,
          legend: {
              position: 'top',
          }
      }
    };
  }

  /**
 * Polar Chart
 */
   private _polarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.polarChart = {
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
          backgroundColor: colors,
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
  }

  /**
 * Redar Chart
 */
   private _radarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.radarChart = {
      labels: ["Eating", "Drinking", "Sleeping", "Designing", "Coding", "Cycling", "Running"],
      datasets: [
          {
              label: "Desktops",
              backgroundColor: colors[0],
              borderColor: colors[1],
              pointBackgroundColor: colors[1],
              pointBorderColor: "#fff",
              pointHoverBackgroundColor: "#fff",
              pointHoverBorderColor: colors[1],
              data: [65, 59, 90, 81, 56, 55, 40]
          },
          {
              label: "Tablets",
              backgroundColor: colors[2],
              borderColor: colors[3], 
              pointBackgroundColor: colors[3],
              pointBorderColor: "#fff",
              pointHoverBackgroundColor: "#fff",
              pointHoverBorderColor: colors[3],
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
   }


}
