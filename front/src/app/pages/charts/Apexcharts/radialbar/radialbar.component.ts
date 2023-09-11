import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-radialbar',
  templateUrl: './radialbar.component.html',
  styleUrls: ['./radialbar.component.scss']
})

/**
 * Apex Radialbar Component
 */
export class RadialbarComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicRadialbarChart: any;
  multipleRadialbarChart: any;
  customAngleChart: any;
  gradientCircleChart: any;
  strokedCircleChart: any;
  radialbarsChart: any;
  semiCircleChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Radialbar Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._basicRadialbarChart('["--vz-success"]');
    this._multipleRadialbarChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger"]');
    this._customAngleChart('["--vz-primary", "--vz-info", "--vz-danger", "--vz-success"]');
    this._gradientCircleChart('["--vz-success"]');
    this._strokedCircleChart('["--vz-success"]');
    this._radialbarsChart('["--vz-success"]');
    this._semiCircleChart('["--vz-primary"]');
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
 * Basic Radialbar Chart
 */
   private _basicRadialbarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.basicRadialbarChart = {
      series: [70],
      chart: {
          height: 350,
          type: "radialBar",
      },
      plotOptions: {
          radialBar: {
              hollow: {
                  size: "70%",
              },
          },
      },
      labels: ["Cricket"],
      colors: colors,
    };
  }

  /**
 * Multiple Radialbar
 */
  private _multipleRadialbarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.multipleRadialbarChart = {
      series: [44, 55, 67, 83],
      chart: {
          height: 350,
          type: "radialBar",
      },
      plotOptions: {
          radialBar: {
              dataLabels: {
                  name: {
                      fontSize: "22px",
                  },
                  value: {
                      fontSize: "16px",
                  },
                  total: {
                      show: true,
                      label: "Total",
                  },
              },
          },
      },
      labels: ["Apples", "Oranges", "Bananas", "Berries"],
      colors: colors,
    };
  }

  /**
 * Circle Chart - Custom Angle
 */
  private _customAngleChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.customAngleChart = {
      series: [76, 67, 61, 55],
      chart: {
          height: 350,
          type: "radialBar",
      },
      plotOptions: {
          radialBar: {
              offsetY: 0,
              startAngle: 0,
              endAngle: 270,
              hollow: {
                  margin: 5,
                  size: "30%",
                  background: "transparent",
                  image: undefined,
              },
              dataLabels: {
                  name: {
                      show: false,
                  },
                  value: {
                      show: false,
                  },
              },
          },
      },
      colors: colors,
      labels: ["Vimeo", "Messenger", "Facebook", "LinkedIn"],
      legend: {
          show: true,
          floating: true,
          fontSize: "16px",
          position: "left",
          offsetX: 160,
          offsetY: 15,
          labels: {
              useSeriesColors: true,
          },
          markers: {

          },
          formatter: function (seriesName:any, opts:any) {
              return seriesName + ":  " + opts.w.globals.series[opts.seriesIndex];
          },
          itemMargin: {
              vertical: 3,
          },
      },
      responsive: [{
          breakpoint: 480,
          options: {
              legend: {
                  show: false,
              },
          },
      }, ],
    };
  }

/**
 * Gradient Circle Chart
 */
  private _gradientCircleChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.gradientCircleChart = {
      series: [75],
      chart: {
          height: 350,
          type: "radialBar",
          toolbar: {
              show: false,
          },
      },
      plotOptions: {
          radialBar: {
              startAngle: -135,
              endAngle: 225,
              hollow: {
                  margin: 0,
                  size: "70%",
                  image: undefined,
                  imageOffsetX: 0,
                  imageOffsetY: 0,
                  position: "front",
              },
              track: {
                  strokeWidth: "67%",
                  margin: 0, // margin is in pixels
              },

              dataLabels: {
                  show: true,
                  name: {
                      offsetY: -10,
                      show: true,
                      color: "#888",
                      fontSize: "17px",
                  },
                  value: {
                      color: "#111",
                      fontSize: "36px",
                      show: true,
                  },
              },
          },
      },
      fill: {
          type: "gradient",
          gradient: {
              shade: "dark",
              type: "horizontal",
              shadeIntensity: 0.5,
              gradientToColors: colors,
              inverseColors: true,
              opacityFrom: 1,
              opacityTo: 1,
              stops: [0, 100],
          },
      },
      stroke: {
          lineCap: "round",
      },
      labels: ["Percent"],
    };
  }

/**
 * Stroked Circular Gauge
 */
  private _strokedCircleChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.strokedCircleChart = {
      series: [67],
      chart: {
          height: 326,
          type: "radialBar",
          offsetY: -10,
      },
      plotOptions: {
          radialBar: {
              startAngle: -135,
              endAngle: 135,
              dataLabels: {
                  name: {
                      fontSize: "16px",
                      color: undefined,
                      offsetY: 120,
                  },
                  value: {
                      offsetY: 76,
                      fontSize: "22px",
                      color: undefined,
                      formatter: function (val:any) {
                          return val + "%";
                      },
                  },
              },
          },
      },
      fill: {
          type: "gradient",
          gradient: {
              shade: "dark",
              shadeIntensity: 0.15,
              inverseColors: false,
              opacityFrom: 1,
              opacityTo: 1,
              stops: [0, 50, 65, 91],
          },
      },
      stroke: {
          dashArray: 4,
      },
      labels: ["Median Ratio"],
      colors: colors,
    };
  }

/**
 * Stroked Circular Gauge
 */
 private _radialbarsChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.radialbarsChart = {
        series: [67],
        chart: {
            height: 315,
            type: 'radialBar',
        },
        plotOptions: {
            radialBar: {
                hollow: {
                    margin: 15,
                    size: '65%',
                    image: './assets/images/comingsoon.png',
                    imageWidth: 56,
                    imageHeight: 56,
                    imageClipped: false
                },
                dataLabels: {
                    name: {
                        show: false,
                        color: '#fff'
                    },
                    value: {
                        show: true,
                        color: '#333',
                        offsetY: 65,
                        fontSize: '22px'
                    }
                }
            }
        },
        fill: {
            type: 'image',
            image: {
                src: ['./assets/images/small/img-4.jpg'],
            }
        },
        stroke: {
            lineCap: 'round'
        },
        labels: ['Volatility'],
    };
 }

/**
 * Semi Circular Gauge
 */
  private _semiCircleChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.semiCircleChart = {
      series: [76],
      chart: {
          type: "radialBar",
          height: 350,
          offsetY: -20,
          sparkline: {
              enabled: true,
          },
      },
      plotOptions: {
          radialBar: {
              startAngle: -90,
              endAngle: 90,
              track: {
                  background: "#e7e7e7",
                  strokeWidth: "97%",
                  margin: 5, // margin is in pixels
                  dropShadow: {
                      enabled: true,
                      top: 2,
                      left: 0,
                      color: "#999",
                      opacity: 1,
                      blur: 2,
                  },
              },
              dataLabels: {
                  name: {
                      show: false,
                  },
                  value: {
                      offsetY: -2,
                      fontSize: "22px",
                  },
              },
          },
      },
      grid: {
          padding: {
              top: -10,
          },
      },
      fill: {
          type: "gradient",
          gradient: {
              shade: "light",
              shadeIntensity: 0.4,
              inverseColors: false,
              opacityFrom: 1,
              opacityTo: 1,
              stops: [0, 50, 53, 91],
          },
      },
      labels: ["Average Results"],
      colors: colors,
    };
  }

}
