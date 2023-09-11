import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss']
})
export class StatisticsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  HiredChart: any;
  ApplicationChart: any;
  InterviewedChart: any;
  RejectedChart: any;
  VisitorChart: any;
  simpleDonutChart: any;
  DealTypeChart: any;
  splineAreaChart: any;

  constructor() {
    // Chart Color Data Get Function
    this._hiredChart('["--vz-success" , "--vz-transparent"]');
    this._applicationChart('["--vz-success" , "--vz-transparent"]');
    this._interviewChart('["--vz-success" , "--vz-transparent"]');
    this._rejectedChart('["--vz-danger", "--vz-transparent"]');
    this._visitorChart('["--vz-primary", "--vz-secondary", "--vz-success", "--vz-info","--vz-warning", "--vz-danger"]');
    this._simpleDonutChart('["--vz-primary", "--vz-warning", "--vz-info"]');
    this._DealTypeChart('["--vz-primary", "--vz-info"]');
    this._splineAreaChart('["--vz-success","--vz-primary", "--vz-info", "--vz-danger"]');
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Jobs' },
      { label: 'Statistics', active: true }
    ];
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
  * Application Chart
  */
  private _applicationChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.ApplicationChart = {
      series: [{
        name: "Results",
        data: [0, 110, 95, 75, 120],
      },],
      chart: {
        width: 140,
        type: "area",
        sparkline: {
          enabled: true,
        },
        toolbar: {
          show: false,
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        curve: "smooth",
        width: 1.5,
      },
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
        },
      },
      colors: colors
    };
  }

  /**
 * Interviewed Chart
 */
  private _interviewChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.InterviewedChart = {
      series: [{
        name: "Results",
        data: [0, 68, 35, 90, 99],
      },],
      chart: {
        width: 140,
        type: "area",
        sparkline: {
          enabled: true,
        },
        toolbar: {
          show: false,
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        curve: "smooth",
        width: 1.5,
      },
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
        },
      },
      colors: colors
    };
  }

  /**
  * Hired Chart
  */
  private _hiredChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.HiredChart = {
      series: [{
        name: "Results",
        data: [0, 36, 110, 95, 130],
      },],
      chart: {
        width: 140,
        type: "area",
        sparkline: {
          enabled: true,
        },
        toolbar: {
          show: false,
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        curve: "smooth",
        width: 1.5,
      },
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
        },
      },
      colors: colors
    };
  }

  /**
   * Rejected Chart
   */
  private _rejectedChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.RejectedChart = {
      series: [{
        name: "Results",
        data: [0, 98, 85, 90, 67],
      },],
      chart: {
        width: 140,
        type: "area",
        sparkline: {
          enabled: true,
        },
        toolbar: {
          show: false,
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        curve: "smooth",
        width: 1.5,
      },
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
        },
      },
      colors: colors
    };
  }

  /**
* Distributed Treemap Chart
*/
  private _visitorChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.VisitorChart = {
      series: [{
        data: [{
          x: 'USA',
          y: 321
        },
        {
          x: 'Russia',
          y: 165
        },
        {
          x: 'India',
          y: 184
        },
        {
          x: 'China',
          y: 98
        },
        {
          x: 'Canada',
          y: 84
        },
        {
          x: 'Brazil',
          y: 31
        },
        {
          x: 'UK',
          y: 70
        },
        {
          x: 'Australia',
          y: 30
        },
        {
          x: 'Germany',
          y: 44
        },
        {
          x: 'Italy',
          y: 68
        },
        {
          x: 'Israel',
          y: 28
        },
        {
          x: 'Indonesia',
          y: 19
        },
        {
          x: 'Bangladesh',
          y: 29
        }
        ]
      }],
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
        text: "Visitors Location",
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
 * Simple Donut Chart
 */
  private _simpleDonutChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.simpleDonutChart = {
      series: [78.56, 105.02, 42.89],
      labels: ["Desktop", "Mobile", "Tablet"],
      chart: {
        type: "donut",
        height: 219,
      },
      plotOptions: {
        pie: {
          donut: {
            size: "76%",
          },
        },
      },
      dataLabels: {
        enabled: false,
      },
      legend: {
        show: false,
        position: 'bottom',
        horizontalAlign: 'center',
        offsetX: 0,
        offsetY: 0,
        markers: {
          width: 20,
          height: 6,
          radius: 2,
        },
        itemMargin: {
          horizontal: 12,
          vertical: 0
        },
      },
      stroke: {
        width: 0
      },
      yaxis: {
        labels: {
          formatter: function (value: any) {
            return value + "k" + " Users";
          }
        },
        tickAmount: 4,
        min: 0
      },
      colors: colors
    };
  }

  /**
  * Deal Type Chart
  */
  private _DealTypeChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.DealTypeChart = {
      series: [{
        name: 'Following',
        data: [80, 50, 30, 40, 100, 20],
      },
      {
        name: 'Followers',
        data: [20, 30, 40, 80, 20, 80],
      }],
      chart: {
        height: 341,
        type: 'radar',
        dropShadow: {
          enabled: true,
          blur: 1, left: 1, top: 1
        },
        toolbar: {
          show: false
        },
      },
      stroke: {
        width: 2
      },
      fill: {
        opacity: 0.2
      },
      legend: {
        show: true,
        fontWeight: 500,
        offsetX: 0,
        offsetY: -8,
        markers: {
          width: 8,
          height: 8,
          radius: 6,
        },
        itemMargin: {
          horizontal: 10,
          vertical: 0
        }
      },
      markers: {
        size: 0
      },
      colors: colors,
      xaxis: {
        categories: ['2016', '2017', '2018', '2019', '2020', '2021']
      }
    };
  }

  /**
  * Splie-Area Chart
  */

  private _splineAreaChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.splineAreaChart = {
      series: [{
        name: 'Application Sent  ',
        data: [33, 28, 30, 35, 40, 55, 70, 110, 150, 180, 210, 250]
      }, {
        name: ' Interviews',
        data: [20, 26, 45, 32, 42, 53, 59, 70, 78, 97, 110, 125]
      },
      {
        name: ' Hired',
        data: [12, 17, 45, 42, 24, 35, 42, 75, 102, 108, 156, 199]
      },
      {
        name: ' Rejected',
        data: [8, 13, 22, 27, 32, 34, 46, 59, 65, 97, 100, 110]
      }],
      chart: {
        height: 320,
        type: 'area',
        toolbar: 'false',
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        curve: 'smooth',
        width: 2,
      },
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      },
      colors: colors,
      fill: {
        opacity: 0.06,
        colors: colors,
        type: 'solid'
      }
    };
  }

}
