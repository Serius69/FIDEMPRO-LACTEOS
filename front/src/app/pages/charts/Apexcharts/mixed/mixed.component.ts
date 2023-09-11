import { Component, OnInit } from '@angular/core';


@Component({
  selector: 'app-mixed',
  templateUrl: './mixed.component.html',
  styleUrls: ['./mixed.component.scss']
})

/**
 * Apex Mixed Component
 */
export class MixedComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  lineChart: any;
  multipleYAxisChart: any;
  lineAreaChart: any;
  lineColumnAreaChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Mixed Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._lineChart('["--vz-primary", "--vz-success"]');
    this._multipleYAxisChart('["--vz-primary", "--vz-info", "--vz-success"]');
    this._lineAreaChart('["--vz-primary", "--vz-success"]');
    this._lineColumnAreaChart('["--vz-primary", "--vz-success", "--vz-danger"]');
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
 * Line & Column Charts
 */
  private _lineChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.lineChart = {
      series: [{
        name: 'Website Blog',
        type: 'column',
        data: [440, 505, 414, 671, 227, 413, 201, 352, 752, 320, 257, 160]
      }, {
          name: 'Social Media',
          type: 'line',
          data: [23, 42, 35, 27, 43, 22, 17, 31, 22, 22, 12, 16]
      }],
      chart: {
        height: 350,
        type: 'line',
        toolbar: {
            show: false,
        }
      },
      stroke: {
          width: [0, 4]
      },
      title: {
          text: 'Traffic Sources',
          style: {
              fontWeight: 600,
          },
      },
      dataLabels: {
          enabled: true,
          enabledOnSeries: [1]
      },
      labels: ['01 Jan 2001', '02 Jan 2001', '03 Jan 2001', '04 Jan 2001', '05 Jan 2001', '06 Jan 2001', '07 Jan 2001', '08 Jan 2001', '09 Jan 2001', '10 Jan 2001', '11 Jan 2001', '12 Jan 2001'],
      xaxis: {
          type: 'datetime'
      },
      yaxis: [{
          title: {
              text: 'Website Blog',
              style: {
                  fontWeight: 600,
              },
          },

      }, {
          opposite: true,
          title: {
              text: 'Social Media',
              style: {
                  fontWeight: 600,
              },
          }
      }],
      colors: colors
    };
  }

  /**
 * Multiple Y-Axis Charts
 */
  private _multipleYAxisChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.multipleYAxisChart = {
      series: [{
        name: 'Income',
        type: 'column',
        data: [1.4, 2, 2.5, 1.5, 2.5, 2.8, 3.8, 4.6]
    }, {
        name: 'Cashflow',
        type: 'column',
        data: [1.1, 3, 3.1, 4, 4.1, 4.9, 6.5, 8.5]
    }, {
        name: 'Revenue',
        type: 'line',
        data: [20, 29, 37, 36, 44, 45, 50, 58]
      }],
      chart: {
          height: 350,
          type: 'line',
          stacked: false,
          toolbar: {
              show: false,
          }
      },
      dataLabels: {
          enabled: false
      },
      stroke: {
          width: [1, 1, 4]
      },
      title: {
          text: 'XYZ - Stock Analysis (2009 - 2016)',
          align: 'left',
          offsetX: 110,
          style: {
              fontWeight: 600,
          },
      },
      xaxis: {
          categories: [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016],
      },
      yaxis: [{
              axisTicks: {
                  show: true,
              },
              axisBorder: {
                  show: true,
                  color: '#405189'
              },
              labels: {
                  style: {
                      colors: '#405189',
                  }
              },
              title: {
                  text: "Income (thousand crores)",
                  style: {
                      color: '#405189',
                      fontWeight: 600
                  }
              },
              tooltip: {
                  enabled: true
              }
          },
          {
              seriesName: 'Income',
              opposite: true,
              axisTicks: {
                  show: true,
              },
              axisBorder: {
                  show: true,
                  color: '#405189'
              },
              labels: {
                  style: {
                      colors: '#405189',
                  }
              },
              title: {
                  text: "Operating Cashflow (thousand crores)",
                  style: {
                      color: '#405189',
                      fontWeight: 600
                  }
              },
          },
          {
              seriesName: 'Revenue',
              opposite: true,
              axisTicks: {
                  show: true,
              },
              axisBorder: {
                  show: true,
                  color: '#63ad6f'
              },
              labels: {
                  style: {
                      colors: '#63ad6f',
                  },
              },
              title: {
                  text: "Revenue (thousand crores)",
                  style: {
                      color: '#63ad6f',
                      fontWeight: 600
                  }
              }
          },
      ],
      tooltip: {
          fixed: {
              enabled: true,
              position: 'topLeft', // topRight, topLeft, bottomRight, bottomLeft
              offsetY: 30,
              offsetX: 60
          },
      },
      legend: {
          horizontalAlign: 'left',
          offsetX: 40
      },
      colors: colors
    };
  }

  /**
 * Line & Area Charts
 */
  private _lineAreaChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.lineAreaChart = {
      series: [{
        name: 'TEAM A',
        type: 'area',
        data: [44, 55, 31, 47, 31, 43, 26, 41, 31, 47, 33]
      }, {
          name: 'TEAM B',
          type: 'line',
          data: [55, 69, 45, 61, 43, 54, 37, 52, 44, 61, 43]
      }],
      chart: {
          height: 350,
          type: 'line',
          toolbar: {
              show: false,
          }
      },
      stroke: {
          curve: 'smooth'
      },
      fill: {
          type: 'solid',
          opacity: [0.35, 1],
      },
      labels: ['Dec 01', 'Dec 02', 'Dec 03', 'Dec 04', 'Dec 05', 'Dec 06', 'Dec 07', 'Dec 08', 'Dec 09 ', 'Dec 10', 'Dec 11'],
      markers: {
          size: 0
      },
      yaxis: [{
              title: {
                  text: 'Series A',
              },
          },
          {
              opposite: true,
              title: {
                  text: 'Series B',
              },
          },
      ],
      tooltip: {
          shared: true,
          intersect: false,
          y: {
              formatter: function (y:any) {
                  if (typeof y !== "undefined") {
                      return y.toFixed(0) + " points";
                  }
                  return y;
              }
          }
      },
      colors: colors
    };
  }

  /**
 * Line, Column & Area Charts
 */
  private _lineColumnAreaChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.lineColumnAreaChart = {
      series: [{
        name: 'TEAM A',
        type: 'column',
        data: [23, 11, 22, 27, 13, 22, 37, 21, 44, 22, 30]
    }, {
        name: 'TEAM B',
        type: 'area',
        data: [44, 55, 41, 67, 22, 43, 21, 41, 56, 27, 43]
    }, {
        name: 'TEAM C',
        type: 'line',
        data: [30, 25, 36, 30, 45, 35, 64, 52, 59, 36, 39]
      }],
      chart: {
          height: 350,
          type: 'line',
          stacked: false,
          toolbar: {
              show: false,
          }
      },
      stroke: {
          width: [0, 2, 5],
          curve: 'smooth'
      },
      plotOptions: {
          bar: {
              columnWidth: '50%'
          }
      },
      fill: {
          opacity: [0.85, 0.25, 1],
          gradient: {
              inverseColors: false,
              shade: 'light',
              type: "vertical",
              opacityFrom: 0.85,
              opacityTo: 0.55,
              stops: [0, 100, 100, 100]
          }
      },
      labels: ['01/01/2003', '02/01/2003', '03/01/2003', '04/01/2003', '05/01/2003', '06/01/2003', '07/01/2003',
          '08/01/2003', '09/01/2003', '10/01/2003', '11/01/2003'
      ],
      markers: {
          size: 0
      },
      xaxis: {
          type: 'datetime'
      },
      yaxis: {
          title: {
              text: 'Points',
          },
          min: 0
      },
      tooltip: {
          shared: true,
          intersect: false,
          y: {
              formatter: function (y:any) {
                  if (typeof y !== "undefined") {
                      return y.toFixed(0) + " points";
                  }
                  return y;

              }
          }
      },
      colors: colors
    };
  }

}
