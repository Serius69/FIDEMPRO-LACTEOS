import { Component, OnInit, ViewChild } from '@angular/core';

import { statData, ActiveProjects, MyTask, TeamMembers } from './data';


@Component({
  selector: 'app-projects',
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.scss']
})

/**
 * Projects Component
 */
export class ProjectsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  statData!: any;
  OverviewChart: any;
  ActiveProjects: any;
  MyTask: any;
  TeamMembers: any;
  status7: any;
  @ViewChild('scrollRef') scrollRef: any;

  constructor() {
  }

  ngOnInit(): void {
    /**
     * BreadCrumb
     */
    this.breadCrumbItems = [
      { label: 'Dashboards' },
      { label: 'Projects', active: true }
    ];

    /**
     * Fetches the data
     */
    this.fetchData();

    // Chart Color Data Get Function
    this._OverviewChart('["--vz-primary", "--vz-warning", "--vz-success"]');
    this._status7('["--vz-success", "--vz-primary", "--vz-warning", "--vz-danger"]');

  }

  ngAfterViewInit() {
    this.scrollRef.SimpleBar.getScrollElement().scrollTop = 600;
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
 * Projects Overview
 */

  setprojectvalue(value: any) {
    if (value == 'all') {
      this.OverviewChart.series = [{
        name: 'Number of Projects',
        type: 'bar',
        data: [34, 65, 46, 68, 49, 61, 42, 44, 78, 52, 63, 67]
      }, {
        name: 'Revenue',
        type: 'area',
        data: [89.25, 98.58, 68.74, 108.87, 77.54, 84.03, 51.24, 28.57, 92.57, 42.36, 88.51, 36.57]
      }, {
        name: 'Active Projects',
        type: 'bar',
        data: [8, 12, 7, 17, 21, 11, 5, 9, 7, 29, 12, 35]
      }]
    }
    if (value == '1M') {
      this.OverviewChart.series = [{
        name: 'Number of Projects',
        type: 'bar',
        data: [24, 75, 16, 98, 19, 41, 52, 34, 28, 52, 63, 67]
      }, {
        name: 'Revenue',
        type: 'area',
        data: [99.25, 28.58, 98.74, 12.87, 107.54, 94.03, 11.24, 48.57, 22.57, 42.36, 88.51, 36.57]
      }, {
        name: 'Active Projects',
        type: 'bar',
        data: [28, 22, 17, 27, 21, 11, 5, 9, 17, 29, 12, 15]
      }]
    }
    if (value == '6M') {
      this.OverviewChart.series = [{
        name: 'Number of Projects',
        type: 'bar',
        data: [34, 75, 66, 78, 29, 41, 32, 44, 58, 52, 43, 77]
      }, {
        name: 'Revenue',
        type: 'area',
        data: [109.25, 48.58, 38.74, 57.87, 77.54, 84.03, 31.24, 18.57, 92.57, 42.36, 48.51, 56.57]
      }, {
        name: 'Active Projects',
        type: 'bar',
        data: [12, 22, 17, 27, 1, 51, 5, 9, 7, 29, 12, 35]
      }]
    }
    if (value == '1Y') {
      this.OverviewChart.series = [{
        name: 'Number of Projects',
        type: 'bar',
        data: [34, 65, 46, 68, 49, 61, 42, 44, 78, 52, 63, 67]
      }, {
        name: 'Revenue',
        type: 'area',
        data: [89.25, 98.58, 68.74, 108.87, 77.54, 84.03, 51.24, 28.57, 92.57, 42.36, 88.51, 36.57]
      }, {
        name: 'Active Projects',
        type: 'bar',
        data: [8, 12, 7, 17, 21, 11, 5, 9, 7, 29, 12, 35]
      }]
    }
  }

  private _OverviewChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.OverviewChart = {
      series: [{
        name: 'Number of Projects',
        type: 'bar',
        data: [34, 65, 46, 68, 49, 61, 42, 44, 78, 52, 63, 67]
      }, {
        name: 'Revenue',
        type: 'area',
        data: [89.25, 98.58, 68.74, 108.87, 77.54, 84.03, 51.24, 28.57, 92.57, 42.36, 88.51, 36.57]
      }, {
        name: 'Active Projects',
        type: 'bar',
        data: [8, 12, 7, 17, 21, 11, 5, 9, 7, 29, 12, 35]
      }],
      chart: {
        height: 374,
        type: 'line',
        toolbar: {
          show: false,
        }
      },
      stroke: {
        curve: 'smooth',
        dashArray: [0, 3, 0],
        width: [0, 1, 0],
      },
      fill: {
        opacity: [1, 0.1, 1]
      },
      markers: {
        size: [0, 4, 0],
        strokeWidth: 2,
        hover: {
          size: 4,
        }
      },
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        axisTicks: {
          show: false
        },
        axisBorder: {
          show: false
        }
      },
      grid: {
        show: true,
        xaxis: {
          lines: {
            show: true,
          }
        },
        yaxis: {
          lines: {
            show: false,
          }
        },
        padding: {
          top: 0,
          right: -2,
          bottom: 15,
          left: 10
        },
      },
      legend: {
        show: true,
        horizontalAlign: 'center',
        offsetX: 0,
        offsetY: -5,
        markers: {
          width: 9,
          height: 9,
          radius: 6,
        },
        itemMargin: {
          horizontal: 10,
          vertical: 0
        },
      },
      plotOptions: {
        bar: {
          columnWidth: '30%',
          barHeight: '70%'
        }
      },
      colors: colors,
      tooltip: {
        shared: true,
        y: [{
          formatter: function (y: any) {
            if (typeof y !== "undefined") {
              return y.toFixed(0);
            }
            return y;

          }
        }, {
          formatter: function (y: any) {
            if (typeof y !== "undefined") {
              return "$" + y.toFixed(2) + "k";
            }
            return y;

          }
        }, {
          formatter: function (y: any) {
            if (typeof y !== "undefined") {
              return y.toFixed(0);
            }
            return y;

          }
        }]
      }
    };
  }

  /**
 *  Status7
 */
  setstatusvalue(value: any) {
    if (value == 'all') {
      this.status7.series = [125, 42, 58, 89]
    }
    if (value == '7') {
      this.status7.series = [25, 52, 158, 99]
    }
    if (value == '30') {
      this.status7.series = [35, 22, 98, 99]
    }
    if (value == '90') {
      this.status7.series = [105, 32, 68, 79]
    }
  }

  private _status7(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.status7 = {
      series: [125, 42, 58, 89],
      labels: ["Completed", "In Progress", "Yet to Start", "Cancelled"],
      chart: {
        type: "donut",
        height: 230,
      },
      plotOptions: {
        pie: {
          offsetX: 0,
          offsetY: 0,
          donut: {
            size: "90%",
            labels: {
              show: false,
            }
          },
        },
      },
      dataLabels: {
        enabled: false,
      },
      legend: {
        show: false,
      },
      stroke: {
        lineCap: "round",
        width: 0
      },
      colors: colors
    };
  }

  /**
   * Fetches the data
   */
  private fetchData() {
    this.statData = statData;
    this.ActiveProjects = ActiveProjects;
    this.MyTask = MyTask;
    this.TeamMembers = TeamMembers;
  }

}
