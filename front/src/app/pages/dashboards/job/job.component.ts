import { Component, OnInit } from '@angular/core';
// Date Format
import { Observable } from 'rxjs';
import { DecimalPipe } from '@angular/common';

// Data Get
import { Recommendedjob, candidate } from './data';
import { JobModel, candidateModel } from './job.model';
import { JobService } from './job.service';
import { NgbdJobSortableHeader } from './job-sortable.directive';

import { circle, latLng, tileLayer } from 'leaflet';

@Component({
  selector: 'app-job',
  templateUrl: './job.component.html',
  styleUrls: ['./job.component.scss'],
  providers: [JobService, DecimalPipe]
})
export class JobComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  basicRadialbarChart: any;
  applyjobChart: any;
  newjobChart: any;
  interviewChart: any;
  hiredChart: any;
  rejectedChart: any;
  dashedLineChart: any;
  Recommendedjobs: any;
  candidatelist!: candidateModel[]
  followbtn: any = 1;
  followtxt: any = 'Follow';

  // Table data
  jobList!: Observable<JobModel[]>;
  total: Observable<number>;
  candidatedetail: any;

  constructor(public service: JobService,) {
    this.jobList = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
       * BreadCrumb
       */
    this.breadCrumbItems = [
      { label: 'Dashboards' },
      { label: 'JOB Dashboard', active: true }
    ];

    // Chart Color Data Get Function
    this._basicRadialbarChart('["--vz-success"]');
    this._ApplyjobChart('["--vz-success"]');
    this._NewjobChart('["--vz-success"]');
    this._InterviewChart('["--vz-danger"]');
    this._HiredChart('["--vz-success"]');
    this._RejectedChart('["--vz-danger"]');
    this._dashedLineChart('["--vz-success", "--vz-info", "--vz-primary"]');

    // Fetch Data
    setTimeout(() => {
      this.jobList.subscribe(x => {
        this.Recommendedjobs = Object.assign([], x);
      });
      this.candidatelist = candidate;
      this.candidatedetail = candidate[0]
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200)
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
* TOTAL JOBS Chart
*/
  private _basicRadialbarChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.basicRadialbarChart = {
      series: [95],
      chart: {
        type: 'radialBar',
        width: 105,
        sparkline: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: false
      },
      plotOptions: {
        radialBar: {
          hollow: {
            margin: 0,
            size: '70%'
          },
          track: {
            margin: 1
          },
          dataLabels: {
            show: true,
            name: {
              show: false
            },
            value: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              offsetY: 8,
            }
          }
        },
      },
      colors: colors,
    };
  }

  //  apply jobs Charts
  private _ApplyjobChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.applyjobChart = {
      series: [97],
      chart: {
        type: 'radialBar',
        width: 105,
        sparkline: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: false
      },
      plotOptions: {
        radialBar: {
          hollow: {
            margin: 0,
            size: '70%'
          },
          track: {
            margin: 1
          },
          dataLabels: {
            show: true,
            name: {
              show: false
            },
            value: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              offsetY: 8,
            }
          }
        },
      },
      colors: colors,
    };
  }

  //  new jobs Charts
  private _NewjobChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.newjobChart = {
      series: [80],
      chart: {
        type: 'radialBar',
        width: 105,
        sparkline: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: false
      },
      plotOptions: {
        radialBar: {
          hollow: {
            margin: 0,
            size: '70%'
          },
          track: {
            margin: 1
          },
          dataLabels: {
            show: true,
            name: {
              show: false
            },
            value: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              offsetY: 8,
            }
          }
        },
      },
      colors: colors,
    };
  }

  //  interview_chart
  private _InterviewChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.interviewChart = {
      series: [89],
      chart: {
        type: 'radialBar',
        width: 105,
        sparkline: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: false
      },
      plotOptions: {
        radialBar: {
          hollow: {
            margin: 0,
            size: '70%'
          },
          track: {
            margin: 1
          },
          dataLabels: {
            show: true,
            name: {
              show: false
            },
            value: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              offsetY: 8,
            }
          }
        },
      },
      colors: colors,
    };
  }

  //  Hired Chart
  private _HiredChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.hiredChart = {
      series: [64],
      chart: {
        type: 'radialBar',
        width: 105,
        sparkline: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: false
      },
      plotOptions: {
        radialBar: {
          hollow: {
            margin: 0,
            size: '70%'
          },
          track: {
            margin: 1
          },
          dataLabels: {
            show: true,
            name: {
              show: false
            },
            value: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              offsetY: 8,
            }
          }
        },
      },
      colors: colors,
    };
  }

  //  Rejected Chart
  private _RejectedChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.rejectedChart = {
      series: [20],
      chart: {
        type: 'radialBar',
        width: 105,
        sparkline: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: false
      },
      plotOptions: {
        radialBar: {
          hollow: {
            margin: 0,
            size: '70%'
          },
          track: {
            margin: 1
          },
          dataLabels: {
            show: true,
            name: {
              show: false
            },
            value: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              offsetY: 8,
            }
          }
        },
      },
      colors: colors,
    };
  }

  //  Dashed line chart

  setapplicationvalue(value: any) {
    if(value == 'All'){
        this.dashedLineChart.series =[{
          name: 'New Application',
          data: [89, 56, 74, 98, 72, 38, 64, 46, 84, 58, 46, 49]
        },
        {
          name: "Interview",
          data: [45, 52, 38, 24, 33, 26, 21, 20, 6, 8, 15, 10]
        },
        {
          name: " Hired",
          data: [36, 42, 60, 42, 13, 18, 29, 37, 36, 51, 32, 35]
        }
        ]
    }
    if(value == '1M'){
        this.dashedLineChart.series = [{
          name: 'New Application',
          data: [45, 52, 38, 24, 33, 26, 21, 20, 6, 8, 15, 10]
        },
        {
          name: "Interview",
          data: [36, 42, 60, 42, 13, 18, 29, 37, 36, 51, 32, 35]
        },
        {
          name: " Hired",
          data: [89, 56, 74, 98, 72, 38, 64, 46, 84, 58, 46, 49]
        }
        ]
      }
    if(value == '6M'){
        this.dashedLineChart.series = [{
          name: 'New Application',
          data: [36, 42, 60, 42, 13, 18, 29, 37, 36, 51, 32, 35]
        },
        {
          name: "Interview",
          data: [45, 52, 38, 24, 33, 26, 21, 20, 6, 8, 15, 10]
        },
        {
          name: " Hired",
          data: [89, 56, 74, 98, 72, 38, 64, 46, 84, 58, 46, 49]
        }
        ]
    }
    if(value == '1Y'){
      this.dashedLineChart.series = [{
        name: 'New Application',
        data: [45, 52, 38, 24, 33, 26, 21, 20, 6, 8, 15, 10]
      },
      {
        name: "Interview",
        data: [36, 42, 60, 42, 13, 18, 29, 37, 36, 51, 32, 35]
      },
      {
        name: " Hired",
        data: [89, 56, 74, 98, 72, 38, 64, 46, 84, 58, 46, 49]
      }
      ]
    }
}


  private _dashedLineChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.dashedLineChart = {
      chart: {
        height: 345,
        type: 'line',
        zoom: {
          enabled: false
        },
        toolbar: {
          show: false,
        }
      },
      colors: colors,
      dataLabels: {
        enabled: false
      },
      stroke: {
        width: [3, 4, 3],
        curve: 'straight',
        dashArray: [0, 8, 5]
      },
      series: [{
        name: 'New Application',
        data: [89, 56, 74, 98, 72, 38, 64, 46, 84, 58, 46, 49]
      },
      {
        name: "Interview",
        data: [45, 52, 38, 24, 33, 26, 21, 20, 6, 8, 15, 10]
      },
      {
        name: " Hired",
        data: [36, 42, 60, 42, 13, 18, 29, 37, 36, 51, 32, 35]
      }
      ],
      markers: {
        size: 0,

        hover: {
          sizeOffset: 6
        }
      },
      xaxis: {
        categories: ['01 Jan', '02 Jan', '03 Jan', '04 Jan', '05 Jan', '06 Jan', '07 Jan', '08 Jan', '09 Jan',
          '10 Jan', '11 Jan', '12 Jan'
        ],
      },
      grid: {
        borderColor: '#f1f1f1',
      }
    };
  }

  /**
     * Sale Location Map
     */
  options = {
    layers: [
      tileLayer("https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoidGhlbWVzYnJhbmQiLCJhIjoiY2xmbmc3bTV4MGw1ejNzbnJqOWpubzhnciJ9.DNkdZVKLnQ6I9NOz7EED-w", {
        id: "mapbox/light-v9",
        tileSize: 512,
        zoomOffset: -1,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
      })
    ],
    zoom: 1.1,
    center: latLng(28, 1.5)
  };
  layers = [
    circle([41.9, 12.45], { color: "#435fe3", opacity: 0.5, weight: 10, fillColor: "#435fe3", fillOpacity: 1, radius: 400000, }),
    circle([12.05, -61.75], { color: "#435fe3", opacity: 0.5, weight: 10, fillColor: "#435fe3", fillOpacity: 1, radius: 400000, }),
    circle([1.3, 103.8], { color: "#435fe3", opacity: 0.5, weight: 10, fillColor: "#435fe3", fillOpacity: 1, radius: 400000, }),
  ];

  // open candidate detail
  opendetail(id: any) {
    this.candidatedetail = this.candidatelist[id]
  }

  // Follow - unfollow
  followClick(ev: any) {
    if (this.followbtn == '1') {
      this.followbtn = '2'
      this.followtxt = 'Unfollow'
    } else {
      this.followbtn = '1'
      this.followtxt = 'Follow'
    }
  }

}
