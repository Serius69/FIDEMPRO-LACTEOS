import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-pie',
  templateUrl: './pie.component.html',
  styleUrls: ['./pie.component.scss']
})

/**
 * Apex Pie Component
 */
export class PieComponent implements OnInit {

   // bread crumb items
   breadCrumbItems!: Array<{}>;
   simplePieChart: any;
  simpleDonutChart: any;
  updatingDonutChart: any;
  monochromePieChart: any;
  gradientDonutChart: any;
  patternedDonutChart: any;
  semiDonutChart: any;
  pieWithImageChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Pie Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._simplePieChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
    this._simpleDonutChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
    this._updatingDonutChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
    this._monochromePieChart('["--vz-primary"]');
    this._gradientDonutChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
    this._patternedDonutChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
    this._pieWithImageChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-info"]');
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
 * Simple Pie Chart
 */
  private _simplePieChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.simplePieChart = {
      series: [44, 55, 13, 43, 22],
      chart: {
        height: 300,
        type: "pie",
      },
      labels: ["Team A", "Team B", "Team C", "Team D", "Team E"],
      legend: {
        position: "bottom",
      },
      dataLabels: {
        dropShadow: {
          enabled: false,
        },
      },
      colors: colors,
    };
  }

  /**
 * Simple Donut Chart
 */
  private _simpleDonutChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.simpleDonutChart = {
      series: [44, 55, 41, 17, 15],
      chart: {
        height: 300,
        type: "donut",
      },
      legend: {
        position: "bottom",
      },
      dataLabels: {
        dropShadow: {
          enabled: false,
        },
      },
      colors: colors,
    };
  }

  // Updating Donut Charts
  private _updatingDonutChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.updatingDonutChart = {
      series: [44, 55, 13, 33],
      chart: {
        height: 280,
        type: "donut",
      },
      dataLabels: {
        enabled: false,
      },
      legend: {
        position: "bottom",
      },
      colors: colors,
    };
  }

  /**
 * Monochrome Pie Chart
 */
  private _monochromePieChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.monochromePieChart = {
      series: [25, 15, 44, 55, 41, 17],
      chart: {
        height: 300,
        type: "pie",
      },
      labels: [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
      ],
      theme: {
        monochrome: {
          enabled: true,
          color: "#405189",
          shadeTo: "light",
          shadeIntensity: 0.6,
        },
      },
      plotOptions: {
        pie: {
          dataLabels: {
            offset: -5,
          },
        },
      },
      title: {
        text: "Monochrome Pie",
        style: {
          fontWeight: 500,
        },
      },
      dataLabels: {
        dropShadow: {
          enabled: false,
        },
      },
      legend: {
        show: false,
      },
    };
  }
  
  /**
 * Gradient Donut Chart
 */
  private _gradientDonutChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.gradientDonutChart = {
      series: [44, 55, 41, 17, 15],
      chart: {
        height: 300,
        type: "donut",
      },
      plotOptions: {
        pie: {
          startAngle: -90,
          endAngle: 270,
        },
      },
      dataLabels: {
        enabled: false,
      },
      fill: {
        type: "gradient",
      },
      legend: {
        position: "bottom",
        formatter: function(val:any, opts:any) {
          return val + " - " + opts.w.globals.series[opts.seriesIndex];
        },
      },
      title: {
        text: "Gradient Donut with custom Start-angle",
        style: {
          fontWeight: 500,
        },
      },
      colors: colors,
    };
  }

  /**
 * Patterned Donut Chart
 */
  private _patternedDonutChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.patternedDonutChart = {
    series: [44, 55, 41, 17, 15],
    chart: {
      height: 300,
      type: "donut",
      dropShadow: {
        enabled: true,
        color: "#111",
        top: -1,
        left: 3,
        blur: 3,
        opacity: 0.2,
      },
    },
    stroke: {
      width: 0,
    },
    plotOptions: {
      pie: {
        donut: {
          labels: {
            show: true,
            total: {
              showAlways: true,
              show: true,
            },
          },
        },
      },
    },
    labels: ["Comedy", "Action", "SciFi", "Drama", "Horror"],
    dataLabels: {
      dropShadow: {
        blur: 3,
        opacity: 0.8,
      },
    },
    fill: {
      type: "pattern",
      opacity: 1,
      pattern: {
        style: [
          "verticalLines",
          "squares",
          "horizontalLines",
          "circles",
          "slantedLines",
        ],
      },
    },
    states: {
      hover: {
      },
    },
    theme: {
      palette: "palette2",
    },
    title: {
      text: "Favourite Movie Type",
      style: {
        fontWeight: 500,
      },
    },
    legend: {
      position: "bottom",
    },
    colors: colors,
    };
  }

  /**
* Pie Chart with Image Fill
*/
private _pieWithImageChart(colors:any) {
  colors = this.getChartColorsArray(colors);
  this.pieWithImageChart = {
    series: [44, 33, 54, 45],
    chart: {
      height: 300,
      type: "pie",
    },
    colors: colors,
    fill: {
      type: "image",
      opacity: 0.85,
      image: {
        src: [
          'assets/images/small/img-3.jpg', 'assets/images/small/img-5.jpg', 'assets/images/small/img-2.jpg',
        ],
        width: 25,
      },
    },
    stroke: {
      width: 4,
    },
    dataLabels: {
      enabled: true,
      style: {
        colors: ["#111"],
      },
      background: {
        enabled: true,
        foreColor: "#fff",
        borderWidth: 0,
      },
    },
    legend: {
      position: "bottom",
    },
  };
}

  

}
