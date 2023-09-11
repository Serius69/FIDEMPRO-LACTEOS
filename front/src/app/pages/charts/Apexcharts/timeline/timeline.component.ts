import { Component, OnInit } from '@angular/core';
import * as moment from 'moment';

@Component({
  selector: 'app-timeline',
  templateUrl: './timeline.component.html',
  styleUrls: ['./timeline.component.scss']
})

/**
 * Apex Timeline Component
 */
export class TimelineComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicTimelineChart: any;
  differentColorChart: any;
  multiSeriesTimelineChart: any;
  advancedTimelineChart: any;
  multipleSeriesChart: any;
  Dumbbell: any
  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Timeline Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._basicTimelineChart('["--vz-primary"]');
    this._differentColorChart('["--vz-primary", "--vz-danger", "--vz-success", "--vz-warning", "--vz-info"]');
    this._multiSeriesTimelineChart('["--vz-primary","--vz-success"]');
    this._advancedTimelineChart('["--vz-primary", "--vz-success", "--vz-warning"]');
    this._multipleSeriesChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info","--vz-gray","--vz-pink","--vz-purple","--vz-secondary", "--vz-body-color"]');
    this._Dumbbell('["--vz-primary", "--vz-success"]')
  }

  // Chart Colors Set
  private getChartColorsArray(colors: any) {
    colors = JSON.parse(colors);
    return colors.map(function (value: any) {
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
 * Basic TimeLine Charts
 */
  private _basicTimelineChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.basicTimelineChart = {
      series: [
        {
          data: [
            {
              x: "Code",
              y: [
                new Date("2019-03-02").getTime(),
                new Date("2019-03-04").getTime(),
              ],
            },
            {
              x: "Test",
              y: [
                new Date("2019-03-04").getTime(),
                new Date("2019-03-08").getTime(),
              ],
            },
            {
              x: "Validation",
              y: [
                new Date("2019-03-08").getTime(),
                new Date("2019-03-12").getTime(),
              ],
            },
            {
              x: "Deployment",
              y: [
                new Date("2019-03-12").getTime(),
                new Date("2019-03-18").getTime(),
              ],
            },
          ],
        },
      ],
      chart: {
        height: 350,
        type: "rangeBar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
        },
      },
      xaxis: {
        type: "datetime",
      },
      colors: colors,
    };
  }

  /**
 * Different Color For Each Bar
 */
  private _differentColorChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.differentColorChart = {
      series: [
        {
          data: [
            {
              x: "Analysis",
              y: [
                new Date("2019-02-27").getTime(),
                new Date("2019-03-04").getTime(),
              ],
              fillColor: colors[0],
            },
            {
              x: "Design",
              y: [
                new Date("2019-03-04").getTime(),
                new Date("2019-03-08").getTime(),
              ],
              fillColor: colors[1],
            },
            {
              x: "Coding",
              y: [
                new Date("2019-03-07").getTime(),
                new Date("2019-03-10").getTime(),
              ],
              fillColor: colors[2],
            },
            {
              x: "Testing",
              y: [
                new Date("2019-03-08").getTime(),
                new Date("2019-03-12").getTime(),
              ],
              fillColor: colors[3],
            },
            {
              x: "Deployment",
              y: [
                new Date("2019-03-12").getTime(),
                new Date("2019-03-17").getTime(),
              ],
              fillColor: colors[4],
            },
          ],
        },
      ],
      chart: {
        height: 330,
        type: "rangeBar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
          distributed: true,
          dataLabels: {
            hideOverflowingLabels: false,
          },
        },
      },
      dataLabels: {
        enabled: true,
        formatter: function (val: any, opts: any) {
          var label = opts.w.globals.labels[opts.dataPointIndex];
          var a = moment(val[0]);
          var b = moment(val[1]);
          var diff = b.diff(a, "days");
          return label + ": " + diff + (diff > 1 ? " days" : " day");
        },
      },
      xaxis: {
        type: "datetime",
      },
      yaxis: {
        show: true,
      },
    };
  }

  /**
 * Multi Series Timeline
 */
  private _multiSeriesTimelineChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.multiSeriesTimelineChart = {
      series: [
        {
          name: "Bob",
          data: [
            {
              x: "Design",
              y: [
                new Date("2019-03-05").getTime(),
                new Date("2019-03-08").getTime(),
              ],
            },
            {
              x: "Code",
              y: [
                new Date("2019-03-08").getTime(),
                new Date("2019-03-11").getTime(),
              ],
            },
            {
              x: "Test",
              y: [
                new Date("2019-03-11").getTime(),
                new Date("2019-03-16").getTime(),
              ],
            },
          ],
        },
        {
          name: "Joe",
          data: [
            {
              x: "Design",
              y: [
                new Date("2019-03-02").getTime(),
                new Date("2019-03-05").getTime(),
              ],
            },
            {
              x: "Code",
              y: [
                new Date("2019-03-06").getTime(),
                new Date("2019-03-09").getTime(),
              ],
            },
            {
              x: "Test",
              y: [
                new Date("2019-03-10").getTime(),
                new Date("2019-03-19").getTime(),
              ],
            },
          ],
        },
      ],
      chart: {
        height: 335,
        type: "rangeBar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
        },
      },
      dataLabels: {
        enabled: true,
        formatter: function (val: any) {
          var a = moment(val[0]);
          var b = moment(val[1]);
          var diff = b.diff(a, "days");
          return diff + (diff > 1 ? " days" : " day");
        },
      },
      fill: {
        type: "gradient",
        gradient: {
          shade: "light",
          type: "vertical",
          shadeIntensity: 0.25,
          gradientToColors: undefined,
          inverseColors: true,
          opacityFrom: 1,
          opacityTo: 1,
          stops: [50, 0, 100, 100],
        },
      },
      xaxis: {
        type: "datetime",
      },
      legend: {
        position: "top",
      },
      colors: colors,
    };
  }

  /**
 * Advanced Timeline (Multiple Range)
 */
  private _advancedTimelineChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.advancedTimelineChart = {
      series: [
        {
          name: "Bob",
          data: [
            {
              x: "Design",
              y: [
                new Date("2019-03-05").getTime(),
                new Date("2019-03-08").getTime(),
              ],
            },
            {
              x: "Code",
              y: [
                new Date("2019-03-02").getTime(),
                new Date("2019-03-05").getTime(),
              ],
            },
            {
              x: "Code",
              y: [
                new Date("2019-03-05").getTime(),
                new Date("2019-03-07").getTime(),
              ],
            },
            {
              x: "Test",
              y: [
                new Date("2019-03-03").getTime(),
                new Date("2019-03-09").getTime(),
              ],
            },
            {
              x: "Test",
              y: [
                new Date("2019-03-08").getTime(),
                new Date("2019-03-11").getTime(),
              ],
            },
            {
              x: "Validation",
              y: [
                new Date("2019-03-11").getTime(),
                new Date("2019-03-16").getTime(),
              ],
            },
            {
              x: "Design",
              y: [
                new Date("2019-03-01").getTime(),
                new Date("2019-03-03").getTime(),
              ],
            },
          ],
        },
        {
          name: "Joe",
          data: [
            {
              x: "Design",
              y: [
                new Date("2019-03-02").getTime(),
                new Date("2019-03-05").getTime(),
              ],
            },
            {
              x: "Test",
              y: [
                new Date("2019-03-06").getTime(),
                new Date("2019-03-16").getTime(),
              ],
            },
            {
              x: "Code",
              y: [
                new Date("2019-03-03").getTime(),
                new Date("2019-03-07").getTime(),
              ],
            },
            {
              x: "Deployment",
              y: [
                new Date("2019-03-20").getTime(),
                new Date("2019-03-22").getTime(),
              ],
            },
            {
              x: "Design",
              y: [
                new Date("2019-03-10").getTime(),
                new Date("2019-03-16").getTime(),
              ],
            },
          ],
        },
        {
          name: "Dan",
          data: [
            {
              x: "Code",
              y: [
                new Date("2019-03-10").getTime(),
                new Date("2019-03-17").getTime(),
              ],
            },
            {
              x: "Validation",
              y: [
                new Date("2019-03-05").getTime(),
                new Date("2019-03-09").getTime(),
              ],
            },
          ],
        },
      ],
      chart: {
        height: 350,
        type: "rangeBar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
          barHeight: "80%",
        },
      },
      xaxis: {
        type: "datetime",
      },
      stroke: {
        width: 1,
      },
      fill: {
        type: "solid",
        opacity: 0.6,
      },
      legend: {
        position: "top",
        horizontalAlign: "left",
      },
      colors: colors,
    };
  }

  /**
  * Advanced Timeline (Multiple Range)
  */
  private _multipleSeriesChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.multipleSeriesChart = {
      series: [
        // George Washington
        {
          name: 'George Washington',
          data: [
            {
              x: 'President',
              y: [
                new Date(1789, 3, 30).getTime(),
                new Date(1797, 2, 4).getTime()
              ]
            },
          ]
        },
        // John Adams
        {
          name: 'John Adams',
          data: [
            {
              x: 'President',
              y: [
                new Date(1797, 2, 4).getTime(),
                new Date(1801, 2, 4).getTime()
              ]
            },
            {
              x: 'Vice President',
              y: [
                new Date(1789, 3, 21).getTime(),
                new Date(1797, 2, 4).getTime()
              ]
            }
          ]
        },
        // Thomas Jefferson
        {
          name: 'Thomas Jefferson',
          data: [
            {
              x: 'President',
              y: [
                new Date(1801, 2, 4).getTime(),
                new Date(1809, 2, 4).getTime()
              ]
            },
            {
              x: 'Vice President',
              y: [
                new Date(1797, 2, 4).getTime(),
                new Date(1801, 2, 4).getTime()
              ]
            },
            {
              x: 'Secretary of State',
              y: [
                new Date(1790, 2, 22).getTime(),
                new Date(1793, 11, 31).getTime()
              ]
            }
          ]
        },
        // Aaron Burr
        {
          name: 'Aaron Burr',
          data: [
            {
              x: 'Vice President',
              y: [
                new Date(1801, 2, 4).getTime(),
                new Date(1805, 2, 4).getTime()
              ]
            }
          ]
        },
        // George Clinton
        {
          name: 'George Clinton',
          data: [
            {
              x: 'Vice President',
              y: [
                new Date(1805, 2, 4).getTime(),
                new Date(1812, 3, 20).getTime()
              ]
            }
          ]
        },
        // John Jay
        {
          name: 'John Jay',
          data: [
            {
              x: 'Secretary of State',
              y: [
                new Date(1789, 8, 25).getTime(),
                new Date(1790, 2, 22).getTime()
              ]
            }
          ]
        },
        // Edmund Randolph
        {
          name: 'Edmund Randolph',
          data: [
            {
              x: 'Secretary of State',
              y: [
                new Date(1794, 0, 2).getTime(),
                new Date(1795, 7, 20).getTime()
              ]
            }
          ]
        },
        // Timothy Pickering
        {
          name: 'Timothy Pickering',
          data: [
            {
              x: 'Secretary of State',
              y: [
                new Date(1795, 7, 20).getTime(),
                new Date(1800, 4, 12).getTime()
              ]
            }
          ]
        },
        // Charles Lee
        {
          name: 'Charles Lee',
          data: [
            {
              x: 'Secretary of State',
              y: [
                new Date(1800, 4, 13).getTime(),
                new Date(1800, 5, 5).getTime()
              ]
            }
          ]
        },
        // John Marshall
        {
          name: 'John Marshall',
          data: [
            {
              x: 'Secretary of State',
              y: [
                new Date(1800, 5, 13).getTime(),
                new Date(1801, 2, 4).getTime()
              ]
            }
          ]
        }
      ],
      chart: {
        height: 350,
        type: 'rangeBar',
        toolbar: {
          show: false,
        }
      },
      plotOptions: {
        bar: {
          horizontal: true,
          barHeight: '35%',
          rangeBarGroupRows: true
        }
      },
      colors: colors,
      fill: {
        type: 'solid'
      },
      xaxis: {
        type: 'datetime'
      },
      legend: {
        position: 'right'
      },
      tooltip: {
        custom: function (opts: any) {
          const fromYear = new Date(opts.y1).getFullYear()
          const toYear = new Date(opts.y2).getFullYear()
          const values = opts.ctx.rangeBar.getTooltipValues(opts)

          return (
            '<div class="apexcharts-tooltip-rangebar">' +
            '<div> <span class="series-name" style="color: ' +
            values.color +
            '">' +
            (values.seriesName ? values.seriesName : '') +
            '</span></div>' +
            '<div> <span class="category">' +
            values.ylabel +
            ' </span> <span class="value start-value">' +
            fromYear +
            '</span> <span class="separator">-</span> <span class="value end-value">' +
            toYear +
            '</span></div>' +
            '</div>'
          )
        }
      }
    };
  }  /**
  * Dumbbell(Multiple Range)
  */
  private _Dumbbell(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.Dumbbell = {
      series: [
        {
          data: [
            {
              x: 'Operations',
              y: [2800, 4500]
            },
            {
              x: 'Customer Success',
              y: [3200, 4100]
            },
            {
              x: 'Engineering',
              y: [2950, 7800]
            },
            {
              x: 'Marketing',
              y: [3000, 4600]
            },
            {
              x: 'Product',
              y: [3500, 4100]
            },
            {
              x: 'Data Science',
              y: [4500, 6500]
            },
            {
              x: 'Sales',
              y: [4100, 5600]
            }
          ]
        }
      ],
      chart: {
        height: 350,
        type: 'rangeBar',
        zoom: {
          enabled: false
        }
      },
      colors: ['#EC7D31', '#36BDCB'],
      plotOptions: {
        bar: {
          horizontal: true,
          isDumbbell: true,
          dumbbellColors: colors
        }
      },
      title: {
        text: 'Paygap Disparity'
      },
      legend: {
        show: true,
        showForSingleSeries: true,
        position: 'top',
        horizontalAlign: 'left',
        customLegendItems: ['Female', 'Male']
      },
      fill: {
        type: 'gradient',
        gradient: {
          gradientToColors: ['#36BDCB'],
          inverseColors: false,
          stops: [0, 100]
        }
      },
      grid: {
        xaxis: {
          lines: {
            show: true
          }
        },
        yaxis: {
          lines: {
            show: false
          }
        }
      }
    };
  }
}