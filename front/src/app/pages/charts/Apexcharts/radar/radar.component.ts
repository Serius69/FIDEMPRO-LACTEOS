import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-radar',
  templateUrl: './radar.component.html',
  styleUrls: ['./radar.component.scss']
})

/**
 * Apex Radar Component
 */
export class RadarComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicRadarChart: any;
  multipleSeriesChart: any;
  polygonFillChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Radar Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._basicRadarChart('["--vz-success"]');
    this._multipleSeriesChart('["--vz-danger", "--vz-success", "--vz-primary"]');
    this._polygonFillChart('["--vz-info"]');
    
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
 * Basic Radar Chart
 */
  private _basicRadarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.basicRadarChart = {
      series: [
        {
          name: "Series 1",
          data: [80, 50, 30, 40, 100, 20],
        },
      ],
      chart: {
        height: 350,
        type: "radar",
        toolbar: {
          show: false,
        },
      },
      stroke: {
        colors: colors,
      },
      xaxis: {
        categories: ["January", "February", "March", "April", "May", "June"],
      },
      colors: colors
    };
  }

  /**
 * Radar Chart - Multiple series
 */
  private _multipleSeriesChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.multipleSeriesChart = {
      series: [
        {
          name: "Series 1",
          data: [80, 50, 30, 40, 100, 20],
        },
        {
          name: "Series 2",
          data: [20, 30, 40, 80, 20, 80],
        },
        {
          name: "Series 3",
          data: [44, 76, 78, 13, 43, 10],
        },
      ],
      chart: {
        height: 350,
        type: "radar",
        dropShadow: {
          enabled: true,
          blur: 1,
          left: 1,
          top: 1,
        },
        toolbar: {
          show: false,
        },
      },
      stroke: {
        width: 2,
      },
      fill: {
        opacity: 0.2,
      },
      markers: {
        size: 0,
      },
      colors: colors,
      xaxis: {
        categories: ["2014", "2015", "2016", "2017", "2018", "2019"],
      },
    };
  }

  /**
 * Radar Chart - Polygon Fill
 */
  private _polygonFillChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.polygonFillChart = {
      series: [
        {
          name: "Series 1",
          data: [20, 100, 40, 30, 50, 80, 33],
        },
      ],
      chart: {
        height: 350,
        type: "radar",
        toolbar: {
          show: false,
        },
      },
      dataLabels: {
        enabled: true,
      },
      plotOptions: {
        radar: {
          size: 140,
        },
      },
      title: {
        text: "Radar with Polygon Fill",
        style: {
          fontWeight: 500,
        },
      },
      colors: colors,
      markers: {
        size: 4,
        colors: ["#fff"],

        strokeWidth: 2,
      },
      tooltip: {
        y: {
          formatter: function(val: any) {
            return val;
          },
        },
      },
      xaxis: {
        categories: [
          "Sunday",
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday",
          "Saturday",
        ],
      },
      yaxis: {
        tickAmount: 7
      },
    };
  }


}
