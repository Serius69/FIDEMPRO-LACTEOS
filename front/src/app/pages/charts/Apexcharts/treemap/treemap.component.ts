import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-treemap',
  templateUrl: './treemap.component.html',
  styleUrls: ['./treemap.component.scss']
})

/**
 * Apex Treemap Component
 */
export class TreemapComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicTreemapChart: any;
  MultiDimensionalChart: any;
  distributedTreemapChart: any;
  colorRangesChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Treemap Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._differentColorChart('["--vz-success"]');
    this._MultiDimensionalChart('["--vz-primary","--vz-success"]');
    this._distributedTreemapChart('["--vz-primary", "--vz-secondary", "--vz-success", "--vz-info","--vz-warning", "--vz-danger"]');
    this._colorRangesChart('["--vz-info","--vz-danger"]');
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
 * Basic Treemap Chart
 */
  private _differentColorChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.basicTreemapChart = {
      series: [{
        data: [{
            x: "New Delhi",
            y: 218,
          },
          {
            x: "Kolkata",
            y: 149,
          },
          {
            x: "Mumbai",
            y: 184,
          },
          {
            x: "Ahmedabad",
            y: 55,
          },
          {
            x: "Bangaluru",
            y: 84,
          },
          {
            x: "Pune",
            y: 31,
          },
          {
            x: "Chennai",
            y: 70,
          },
          {
            x: "Jaipur",
            y: 30,
          },
          {
            x: "Surat",
            y: 44,
          },
          {
            x: "Hyderabad",
            y: 68,
          },
          {
            x: "Lucknow",
            y: 28,
          },
          {
            x: "Indore",
            y: 19,
          },
          {
            x: "Kanpur",
            y: 29,
          },
        ],
      }, ],
      legend: {
        show: false,
      },
      chart: {
        height: 350,
        type: "treemap",
        toolbar: {
          show: false,
        },
      },
      colors: colors,
      title: {
        text: "Basic Treemap",
        style: {
          fontWeight: 500,
        },
      },
    };
  }

  /**
 * Multi-Dimensional Treemap Chart
 */
  private _MultiDimensionalChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.MultiDimensionalChart = {
      series: [{
        name: "Desktops",
        data: [{
            x: "ABC",
            y: 10,
          },
          {
            x: "DEF",
            y: 60,
          },
          {
            x: "XYZ",
            y: 41,
          },
        ],
      },
      {
        name: "Mobile",
        data: [{
            x: "ABCD",
            y: 10,
          },
          {
            x: "DEFG",
            y: 20,
          },
          {
            x: "WXYZ",
            y: 51,
          },
          {
            x: "PQR",
            y: 30,
          },
          {
            x: "MNO",
            y: 20,
          },
          {
            x: "CDE",
            y: 30,
          },
        ],
      },
      ],
      legend: {
        show: false,
      },
      chart: {
        height: 350,
        type: "treemap",
        toolbar: {
          show: false,
        },
      },
      title: {
        text: "Multi-dimensional Treemap",
        align: "center",
        style: {
          fontWeight: 500,
        },
      },
      colors: colors,
    };
  }

  /**
 * Distributed Treemap Chart
 */
  private _distributedTreemapChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.distributedTreemapChart = {
      series: [{
        data: [{
            x: "New Delhi",
            y: 218,
          },
          {
            x: "Kolkata",
            y: 149,
          },
          {
            x: "Mumbai",
            y: 184,
          },
          {
            x: "Ahmedabad",
            y: 55,
          },
          {
            x: "Bangaluru",
            y: 84,
          },
          {
            x: "Pune",
            y: 31,
          },
          {
            x: "Chennai",
            y: 70,
          },
          {
            x: "Jaipur",
            y: 30,
          },
          {
            x: "Surat",
            y: 44,
          },
          {
            x: "Hyderabad",
            y: 68,
          },
          {
            x: "Lucknow",
            y: 28,
          },
          {
            x: "Indore",
            y: 19,
          },
          {
            x: "Kanpur",
            y: 29,
          },
        ],
      }, ],
      legend: {
        show: false,
      },
      chart: {
        height: 350,
        type: "treemap",
        toolbar: {
          show: false,
        },
      },
      title: {
        text: "Distibuted Treemap (different color for each cell)",
        align: "center",
        style: {
          fontWeight: 500,
        },
      },
      colors: colors,
      plotOptions: {
        treemap: {
          distributed: true,
          enableShades: false,
        },
      },
    };
  }

  /**
 * Treemap Chart with Color Ranges
 */
  private _colorRangesChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.colorRangesChart = {
      series: [{
        data: [{
            x: "INTC",
            y: 1.2,
          },
          {
            x: "GS",
            y: 0.4,
          },
          {
            x: "CVX",
            y: -1.4,
          },
          {
            x: "GE",
            y: 2.7,
          },
          {
            x: "CAT",
            y: -0.3,
          },
          {
            x: "RTX",
            y: 5.1,
          },
          {
            x: "CSCO",
            y: -2.3,
          },
          {
            x: "JNJ",
            y: 2.1,
          },
          {
            x: "PG",
            y: 0.3,
          },
          {
            x: "TRV",
            y: 0.12,
          },
          {
            x: "MMM",
            y: -2.31,
          },
          {
            x: "NKE",
            y: 3.98,
          },
          {
            x: "IYT",
            y: 1.67,
          },
        ],
      }, ],
      legend: {
        show: false,
      },
      chart: {
        height: 350,
        type: "treemap",
        toolbar: {
          show: false,
        },
      },
      title: {
        text: "Treemap with Color scale",
        style: {
          fontWeight: 500,
        },
      },
      dataLabels: {
        enabled: true,
        style: {
          fontSize: "12px",
        },
        offsetY: -4,
      },
      plotOptions: {
        treemap: {
          enableShades: true,
          shadeIntensity: 0.5,
          reverseNegativeShade: true,
          colorScale: {
            ranges: [{
                from: -6,
                to: 0,
                color: colors[0],
              },
              {
                from: 0.001,
                to: 6,
                color: colors[1],
              },
            ],
          },
        },
      },
    };
  }

}
