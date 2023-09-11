import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-scatter',
  templateUrl: './scatter.component.html',
  styleUrls: ['./scatter.component.scss']
})

/**
 * Apex Scatter Component
 */
export class ScatterComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicScatterChart: any;
  dateTimeScatterChart: any;
  ScatterImagesChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Scatter Charts', active: true }
    ];
    
    // Chart Color Data Get Function
    this._basicScatterChart('["--vz-primary", "--vz-success", "--vz-warning"]');
    this._dateTimeScatterChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-warning", "--vz-info"]');
    this._ScatterImagesChart('["--vz-primary", "--vz-danger"]');
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
 * Series Data
 */
private generateDayWiseTimeSeries(baseval: number, count: number, yrange: { max: number; min: number; }) {
  var i = 0;
  var series = [];
  while (i < count) {
      var y =
          Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

      series.push([baseval, y]);
      baseval += 86400000;
      i++;
  }
  return series;
}

  /**
 * Basic Scatter Chart
 */
  private _basicScatterChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.basicScatterChart = {
      series: [{
        name: "SAMPLE A",
        data: [
            [16.4, 5.4],
            [21.7, 2],
            [25.4, 3],
            [19, 2],
            [10.9, 1],
            [13.6, 3.2],
            [10.9, 7.4],
            [10.9, 0],
            [10.9, 8.2],
            [16.4, 0],
            [16.4, 1.8],
            [13.6, 0.3],
            [13.6, 0],
            [29.9, 0],
            [27.1, 2.3],
            [16.4, 0],
            [13.6, 3.7],
            [10.9, 5.2],
            [16.4, 6.5],
            [10.9, 0],
            [24.5, 7.1],
            [10.9, 0],
            [8.1, 4.7],
            [19, 0],
            [21.7, 1.8],
            [27.1, 0],
            [24.5, 0],
            [27.1, 0],
            [29.9, 1.5],
            [27.1, 0.8],
            [22.1, 2],
        ],
    },
    {
        name: "SAMPLE B",
        data: [
            [36.4, 13.4],
            [1.7, 11],
            [5.4, 8],
            [9, 17],
            [1.9, 4],
            [3.6, 12.2],
            [1.9, 14.4],
            [1.9, 9],
            [1.9, 13.2],
            [1.4, 7],
            [6.4, 8.8],
            [3.6, 4.3],
            [1.6, 10],
            [9.9, 2],
            [7.1, 15],
            [1.4, 0],
            [3.6, 13.7],
            [1.9, 15.2],
            [6.4, 16.5],
            [0.9, 10],
            [4.5, 17.1],
            [10.9, 10],
            [0.1, 14.7],
            [9, 10],
            [12.7, 11.8],
            [2.1, 10],
            [2.5, 10],
            [27.1, 10],
            [2.9, 11.5],
            [7.1, 10.8],
            [2.1, 12],
        ],
    },
    {
        name: "SAMPLE C",
        data: [
            [21.7, 3],
            [23.6, 3.5],
            [24.6, 3],
            [29.9, 3],
            [21.7, 20],
            [23, 2],
            [10.9, 3],
            [28, 4],
            [27.1, 0.3],
            [16.4, 4],
            [13.6, 0],
            [19, 5],
            [22.4, 3],
            [24.5, 3],
            [32.6, 3],
            [27.1, 4],
            [29.6, 6],
            [31.6, 8],
            [21.6, 5],
            [20.9, 4],
            [22.4, 0],
            [32.6, 10.3],
            [29.7, 20.8],
            [24.5, 0.8],
            [21.4, 0],
            [21.7, 6.9],
            [28.6, 7.7],
            [15.4, 0],
            [18.1, 0],
            [33.4, 0],
            [16.4, 0],
        ],
    },
      ],
      chart: {
          height: 350,
          type: "scatter",
          zoom: {
              enabled: true,
              type: "xy",
          },
          toolbar: {
              show: false,
          },
      },
      xaxis: {
          tickAmount: 10,
          labels: {
              formatter: function (val:any) {
                  return parseFloat(val).toFixed(1);
              },
          },
      },
      yaxis: {
          tickAmount: 7,
      },
      colors: colors,

    };
  }

  /**
 * Scatter - Datetime Chart
 */
  private _dateTimeScatterChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.dateTimeScatterChart = {
      series: [{
        name: "TEAM 1",
        data: this.generateDayWiseTimeSeries(
            new Date("11 Feb 2017 GMT").getTime(),
            20, {
                min: 10,
                max: 60,
            }
        ),
    },
    {
        name: "TEAM 2",
        data: this.generateDayWiseTimeSeries(
            new Date("11 Feb 2017 GMT").getTime(),
            20, {
                min: 10,
                max: 60,
            }
        ),
    },
    {
        name: "TEAM 3",
        data: this.generateDayWiseTimeSeries(
            new Date("11 Feb 2017 GMT").getTime(),
            30, {
                min: 10,
                max: 60,
            }
        ),
    },
    {
        name: "TEAM 4",
        data: this.generateDayWiseTimeSeries(
            new Date("11 Feb 2017 GMT").getTime(),
            10, {
                min: 10,
                max: 60,
            }
        ),
    },
    {
        name: "TEAM 5",
        data: this.generateDayWiseTimeSeries(
            new Date("11 Feb 2017 GMT").getTime(),
            30, {
                min: 10,
                max: 60,
            }
        ),
    },
      ],
      chart: {
          height: 350,
          type: "scatter",
          zoom: {
              type: "xy",
          },
          toolbar: {
              show: false,
          },
      },
      dataLabels: {
          enabled: false,
      },
      grid: {
          xaxis: {
              lines: {
                  show: true,
              },
          },
          yaxis: {
              lines: {
                  show: true,
              },
          },
      },
      xaxis: {
          type: "datetime",
      },
      yaxis: {
          max: 70,
      },
      colors: colors,
    };
  }

  /**
 * Scatter Images Chart
 */
  private _ScatterImagesChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.ScatterImagesChart = {
      series: [{
        name: "User A",
        data: [
            [16.4, 5.4],
            [21.7, 4],
            [25.4, 3],
            [19, 2],
            [10.9, 1],
            [13.6, 3.2],
            [10.9, 7],
            [10.9, 8.2],
            [16.4, 4],
            [13.6, 4.3],
            [13.6, 12],
            [29.9, 3],
            [10.9, 5.2],
            [16.4, 6.5],
            [10.9, 8],
            [24.5, 7.1],
            [10.9, 7],
            [8.1, 4.7],
        ],
      },
      {
          name: "User B",
          data: [
              [6.4, 5.4],
              [11.7, 4],
              [15.4, 3],
              [9, 2],
              [10.9, 11],
              [20.9, 7],
              [12.9, 8.2],
              [6.4, 14],
              [11.6, 12],
          ],
      },
      ],
        chart: {
            height: 350,
            type: "scatter",
            animations: {
                enabled: false
            },
            zoom: {
                enabled: false
            },
            toolbar: {
                show: false
            }
        },
        colors: colors,
        xaxis: {
            tickAmount: 10,
            min: 0,
            max: 40,
            labels: {
                rotate: 0,
                trim: false
            }
        },
        yaxis: {
            tickAmount: 7
        },
        markers: {
            size: 20
        },
        fill: {
            type: "image",
            opacity: 1,
            image: {
                src: [
                    "assets/images/users/avatar-1.jpg",
                    "assets/images/users/avatar-2.jpg"
                ],
                width: 40,
                height: 40
            }
        },
        legend: {
            labels: {
                useSeriesColors: true
            },
            markers: {
                customHTML: [
                    function () {
                        return '<span><i class="fab fa-facebook"></i></span>';
                    },
                    function () {
                        return '<span><i class="fab fa-instagram"></i></span>';
                    }
                ]
            }
        }
    };
  }

}
