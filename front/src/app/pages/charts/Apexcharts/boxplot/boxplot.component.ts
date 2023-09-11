import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-boxplot',
  templateUrl: './boxplot.component.html',
  styleUrls: ['./boxplot.component.scss']
})

/**
 * Apex Boxplot Component
 */
export class BoxplotComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicBoxChart: any;
  scatterBoxChart: any;
  horizontalBoxChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Boxplot Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._basicBoxChart('["--vz-primary", "--vz-info"]');
    this._scatterBoxChart('["--vz-danger", "--vz-info", "--vz-danger", "--vz-primary"]');
    this._horizontalBoxChart('["--vz-light", "--vz-secondary-bg"]');
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
 * Basic Box Chart
 */
  private _basicBoxChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.basicBoxChart = {
      series: [
        {
          type: "boxPlot",
          data: [
            {
              x: "Jan 2015",
              y: [54, 66, 69, 75, 88],
            },
            {
              x: "Jan 2016",
              y: [43, 65, 69, 76, 81],
            },
            {
              x: "Jan 2017",
              y: [31, 39, 45, 51, 59],
            },
            {
              x: "Jan 2018",
              y: [39, 46, 55, 65, 71],
            },
            {
              x: "Jan 2019",
              y: [29, 31, 35, 39, 44],
            },
            {
              x: "Jan 2020",
              y: [41, 49, 58, 61, 67],
            },
            {
              x: "Jan 2021",
              y: [54, 59, 66, 71, 88],
            },
          ],
        },
      ],
      chart: {
        type: "boxPlot",
        height: 350,
        toolbar: {
          show: false,
        },
      },
      title: {
        text: "Basic BoxPlot Chart",
        align: "left",
        style: {
          fontWeight: 500,
        },
      },
      plotOptions: {
        boxPlot: {
          colors: {
            upper: colors[0],
            lower: colors[1],
          },
        },
      },

    };
  }

  /**
 * Boxplot with Scatter Chart
 */
  private _scatterBoxChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.scatterBoxChart = {
      series: [
        {
          name: "Box",
          type: "boxPlot",
          data: [
            {
              x: new Date("2017-01-01").getTime(),
              y: [54, 66, 69, 75, 88],
            },
            {
              x: new Date("2018-01-01").getTime(),
              y: [43, 65, 69, 76, 81],
            },
            {
              x: new Date("2019-01-01").getTime(),
              y: [31, 39, 45, 51, 59],
            },
            {
              x: new Date("2020-01-01").getTime(),
              y: [39, 46, 55, 65, 71],
            },
            {
              x: new Date("2021-01-01").getTime(),
              y: [29, 31, 35, 39, 44],
            },
          ],
        },
        {
          name: "Outliers",
          type: "scatter",
          data: [
            {
              x: new Date("2017-01-01").getTime(),
              y: 32,
            },
            {
              x: new Date("2018-01-01").getTime(),
              y: 25,
            },
            {
              x: new Date("2019-01-01").getTime(),
              y: 64,
            },
            {
              x: new Date("2020-01-01").getTime(),
              y: 27,
            },
            {
              x: new Date("2020-01-01").getTime(),
              y: 78,
            },
            {
              x: new Date("2021-01-01").getTime(),
              y: 15,
            },
          ],
        },
      ],
      chart: {
        type: "boxPlot",
        height: 350,
        toolbar: {
          show: false,
        },
      },
      colors: [colors[0], colors[1]],
      title: {
        text: "BoxPlot - Scatter Chart",
        align: "left",
        style: {
          fontWeight: 500,
        },
      },
      xaxis: {
        type: "datetime",
        tooltip: {

        },
      },
      plotOptions: {
        boxPlot: {
          colors: {
            upper: colors[2],
            lower: colors[3],
          },
        },
      },
      tooltip: {
        shared: false,
        intersect: true,
      },
    };
  }

  /**
  * Boxplot with Horizontal Chart
  */
  private _horizontalBoxChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.horizontalBoxChart = {
      series: [
        {
          data: [
            {
              x: 'Category A',
              y: [54, 66, 69, 75, 88]
            },
            {
              x: 'Category B',
              y: [43, 65, 69, 76, 81]
            },
            {
              x: 'Category C',
              y: [31, 39, 45, 51, 59]
            },
            {
              x: 'Category D',
              y: [39, 46, 55, 65, 71]
            },
            {
              x: 'Category E',
              y: [29, 31, 35, 39, 44]
            },
            {
              x: 'Category F',
              y: [41, 49, 58, 61, 67]
            },
            {
              x: 'Category G',
              y: [54, 59, 66, 71, 88]
            }
          ]
        }
      ],
      chart: {
        type: 'boxPlot',
        height: 350,
        toolbar: {
          show: false
        }
      },
      plotOptions: {
        bar: {
          horizontal: true,
          barHeight: '50%'
        },
        boxPlot: {
          colors: {
            upper: colors[0],
            lower: colors[1]
          }
        }
      },

      stroke: {
        colors: [colors[0]]
      },
    };
  }

}
