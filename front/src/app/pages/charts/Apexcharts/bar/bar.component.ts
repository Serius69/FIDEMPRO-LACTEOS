import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-bar',
  templateUrl: './bar.component.html',
  styleUrls: ['./bar.component.scss']
})

/**
 * Apex Bar Component
 */
export class BarComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicBarChart: any;
  customDataLabelsChart: any;
  stackedBarChart: any;
  stacked100BarChart: any;
  barWithNegativeChart: any;
  barWithMarkersChart: any;
  reversedBarChart: any;
  patternedChart: any;
  groupedBarChart: any;
  barWithImageChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Bar Charts', active: true }
    ];

     // Chart Color Data Get Function
     this._basicBarChart('["--vz-success"]');
     this._customDataLabelsChart('["--vz-primary", "--vz-secondary", "--vz-success", "--vz-info", "--vz-warning", "--vz-danger", "--vz-body-color", "--vz-primary", "--vz-success", "--vz-secondary"]');
     this._stackedBarChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
     this._stacked100BarChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
     this._barWithNegativeChart('["--vz-primary", "--vz-success"]');
     this._barWithMarkersChart('["--vz-success", "--vz-primary"]');
     this._reversedBarChart('["--vz-info"]');
     this._patternedChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger"]');
     this._groupedBarChart('["--vz-primary", "--vz-success"]');
     this._barWithImageChart('["--vz-success"]');
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
   * Basic Bar Chart
   */
  private _basicBarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.basicBarChart = {
      series: [{
        data: [380, 430, 450, 475, 550, 584, 780, 1100, 1220, 1365],
      }, ],
      chart: {
        height: 350,
        type: "bar",
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
        enabled: false,
      },
      colors: colors,
      grid: {
        borderColor: "#f1f1f1",
      },
      xaxis: {
        categories: [
          "South Korea",
          "Canada",
          "United Kingdom",
          "Netherlands",
          "Italy",
          "France",
          "Japan",
          "United States",
          "China",
          "Germany",
        ],
      },
    };
  }

  /**
 * Custom DataLabels Bar
 */
   private _customDataLabelsChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.customDataLabelsChart = {
      series: [{
        data: [400, 430, 448, 470, 540, 580, 690, 1100, 1200, 1380],
      }, ],
      chart: {
        type: "bar",
        height: 350,
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          barHeight: "100%",
          distributed: true,
          horizontal: true,
          dataLabels: {
            position: "bottom",
          },
        },
      },
      colors: colors,
      dataLabels: {
        enabled: true,
        textAnchor: "start",
        style: {
          colors: ["#fff"],
        },
        formatter: function (val:any, opt:any) {
          return opt.w.globals.labels[opt.dataPointIndex] + ":  " + val;
        },
        offsetX: 0,
        dropShadow: {
          enabled: false,
        },
      },
      stroke: {
        width: 1,
        colors: ["#fff"],
      },
      xaxis: {
        categories: [
          "South Korea",
          "Canada",
          "United Kingdom",
          "Netherlands",
          "Italy",
          "France",
          "Japan",
          "United States",
          "China",
          "India",
        ],
      },
      yaxis: {
        labels: {
          show: false,
        },
      },
      title: {
        text: "Custom DataLabels",
        align: "center",
        floating: true,
        style: {
          fontWeight: 600,
        },
      },
      subtitle: {
        text: "Category Names as DataLabels inside bars",
        align: "center",
      },
      tooltip: {
        theme: "dark",
        x: {
          show: false,
        },
        y: {
          title: {
            formatter: function () {
              return "";
            },
          },
        },
      },
    };
  }

  /**
 * Stacked Bar Charts
   */
  private _stackedBarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.stackedBarChart = {
      series: [{
        name: "Marine Sprite",
        data: [44, 55, 41, 37, 22, 43, 21],
      },
      {
        name: "Striking Calf",
        data: [53, 32, 33, 52, 13, 43, 32],
      },
      {
        name: "Tank Picture",
        data: [12, 17, 11, 9, 15, 11, 20],
      },
      {
        name: "Bucket Slope",
        data: [9, 7, 5, 8, 6, 9, 4],
      },
      {
        name: "Reborn Kid",
        data: [25, 12, 19, 32, 25, 24, 10],
      },
      ],
      chart: {
        type: "bar",
        height: 350,
        stacked: true,
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
        },
      },
      stroke: {
        width: 1,
        colors: ["#fff"],
      },
      title: {
        text: "Fiction Books Sales",
        style: {
          fontWeight: 600,
        },
      },
      xaxis: {
        categories: [2008, 2009, 2010, 2011, 2012, 2013, 2014],
        labels: {
          formatter: function (val:any) {
            return val + "K";
          },
        },
      },
      yaxis: {
        title: {
          text: undefined,
        },
      },
      tooltip: {
        y: {
          formatter: function (val:any) {
            return val + "K";
          },
        },
      },
      fill: {
        opacity: 1,
      },
      legend: {
        position: "top",
        horizontalAlign: "left",
        offsetX: 40,
      },
      colors: colors,
    };
  }

  /**
 * Stacked 100 Bar Charts
 */
   private _stacked100BarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.stacked100BarChart = {
      series: [{
        name: "Marine Sprite",
        data: [44, 55, 41, 37, 22, 43, 21],
      },
      {
        name: "Striking Calf",
        data: [53, 32, 33, 52, 13, 43, 32],
      },
      {
        name: "Tank Picture",
        data: [12, 17, 11, 9, 15, 11, 20],
      },
      {
        name: "Bucket Slope",
        data: [9, 7, 5, 8, 6, 9, 4],
      },
      {
        name: "Reborn Kid",
        data: [25, 12, 19, 32, 25, 24, 10],
      },
      ],
      chart: {
        type: "bar",
        height: 350,
        stacked: true,
        stackType: "100%",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
        },
      },
      stroke: {
        width: 1,
        colors: ["#fff"],
      },
      title: {
        text: "100% Stacked Bar",
        style: {
          fontWeight: 600,
        },
      },
      xaxis: {
        categories: [2008, 2009, 2010, 2011, 2012, 2013, 2014],
      },
      tooltip: {
        y: {
          formatter: function (val:any) {
            return val + "K";
          },
        },
      },
      fill: {
        opacity: 1,
      },
      legend: {
        position: "top",
        horizontalAlign: "left",
        offsetX: 40,
      },
      colors: colors,
    };
   }

  /**
 * Bar with Negative Values
 */
   private _barWithNegativeChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.barWithNegativeChart = {
      series: [{
        name: "Males",
        data: [
          0.4,
          0.65,
          0.76,
          0.88,
          1.5,
          2.1,
          2.9,
          3.8,
          3.9,
          4.2,
          4,
          4.3,
          4.1,
          4.2,
          4.5,
          3.9,
          3.5,
          3,
        ],
      },
      {
        name: "Females",
        data: [
          -0.8,
          -1.05,
          -1.06,
          -1.18,
          -1.4,
          -2.2,
          -2.85,
          -3.7,
          -3.96,
          -4.22,
          -4.3,
          -4.4,
          -4.1,
          -4,
          -4.1,
          -3.4,
          -3.1,
          -2.8,
        ],
      },
    ],
      chart: {
        type: "bar",
        height: 360,
        stacked: true,
        toolbar: {
          show: false,
        },
      },
      colors: colors,
      plotOptions: {
        bar: {
          horizontal: true,
          barHeight: "80%",
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        width: 1,
        colors: ["#fff"],
      },
      grid: {
        xaxis: {
          lines: {
            show: false,
          },
        },
      },
      yaxis: {
        min: -5,
        max: 5,
        title: {
          text: "Age",
          style: {
            fontWeight: 600,
          },
        },
      },
      tooltip: {
        shared: false,
        x: {

        },
        y: {
          formatter: function (val:any) {
            return Math.abs(val) + "%";
          },
        },
      },
      title: {
        text: "Mauritius population pyramid 2011",
        style: {
          fontWeight: 600,
        },
      },
      xaxis: {
        categories: [
          "85+",
          "80-84",
          "75-79",
          "70-74",
          "65-69",
          "60-64",
          "55-59",
          "50-54",
          "45-49",
          "40-44",
          "35-39",
          "30-34",
          "25-29",
          "20-24",
          "15-19",
          "10-14",
          "5-9",
          "0-4",
        ],
        title: {
          text: "Percent",
        },
        labels: {

        },
      },
    };
   }

  /**
 * Bar with Markers
 */
  private _barWithMarkersChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.barWithMarkersChart = {
      series: [{
        name: "Actual",
        data: [{
            x: "2011",
            y: 12,
            goals: [{
              name: "Expected",
              value: 14,
              strokeWidth: 5,
              strokeColor: "#564ab1",
            }, ],
          },
          {
            x: "2012",
            y: 44,
            goals: [{
              name: "Expected",
              value: 54,
              strokeWidth: 5,
              strokeColor: "#564ab1",
            }, ],
          },
          {
            x: "2013",
            y: 54,
            goals: [{
              name: "Expected",
              value: 52,
              strokeWidth: 5,
              strokeColor: "#564ab1",
            }, ],
          },
          {
            x: "2014",
            y: 66,
            goals: [{
              name: "Expected",
              value: 65,
              strokeWidth: 5,
              strokeColor: "#564ab1",
            }, ],
          },
          {
            x: "2015",
            y: 81,
            goals: [{
              name: "Expected",
              value: 66,
              strokeWidth: 5,
              strokeColor: "#564ab1",
            }, ],
          },
          {
            x: "2016",
            y: 67,
            goals: [{
              name: "Expected",
              value: 70,
              strokeWidth: 5,
              strokeColor: "#564ab1",
            }, ],
          },
        ],
        }, ],
        chart: {
          height: 350,
          type: "bar",
          toolbar: {
            show: false,
          },
        },
        plotOptions: {
          bar: {
            horizontal: true,
          },
        },
        colors: colors,
        dataLabels: {
            formatter: function (val:any) {
                return val.toString();
            }
        },
        legend: {
          show: true,
          showForSingleSeries: true,
          customLegendItems: ["Actual", "Expected"],
          markers: {
            fillColors: ["#0AB39C", "#0AB39C"],
          },
        },
    };
  }

  /**
 * Reversed Bar Chart
 */
   private _reversedBarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.reversedBarChart = {
      series: [{
        data: [400, 430, 448, 470, 540, 580, 690],
      }, ],
      chart: {
        type: "bar",
        height: 350,
        toolbar: {
          show: false,
        },
      },
      annotations: {
        xaxis: [{
          x: 500,
          borderColor: "#299CDB",
          label: {
            borderColor: "#299CDB",
            style: {
              color: "#fff",
              background: "#299CDB",
            },
            text: "X annotation",
          },
        }, ],
        yaxis: [{
          y: "July",
          y2: "September",
          label: {
            text: "Y annotation",
          },
        }, ],
      },
      plotOptions: {
        bar: {
          horizontal: true,
        },
      },
      dataLabels: {
        enabled: true,
      },
      xaxis: {
        categories: [
          "June",
          "July",
          "August",
          "September",
          "October",
          "November",
          "December",
        ],
      },
      grid: {
        xaxis: {
          lines: {
            show: true,
          },
        },
      },
      yaxis: {
        reversed: true,
        axisTicks: {
          show: true,
        },
      },
      colors: colors
    };
   }

   /**
 * Patterned Chart
 */
    private _patternedChart(colors:any) {
      colors = this.getChartColorsArray(colors);
      this.patternedChart = {
        series: [{
          name: "Marine Sprite",
          data: [44, 55, 41, 37, 22, 43, 21],
        },
        {
          name: "Striking Calf",
          data: [53, 32, 33, 52, 13, 43, 32],
        },
        {
          name: "Tank Picture",
          data: [12, 17, 11, 9, 15, 11, 20],
        },
        {
          name: "Bucket Slope",
          data: [9, 7, 5, 8, 6, 9, 4],
        },
        ],
        chart: {
          type: "bar",
          height: 350,
          stacked: true,
          dropShadow: {
            enabled: true,
            blur: 1,
            opacity: 0.25,
          },
          toolbar: {
            show: false,
          },
        },
        plotOptions: {
          bar: {
            horizontal: true,
            barHeight: "60%",
          },
        },
        dataLabels: {
          enabled: false,
        },
        stroke: {
          width: 2,
        },
        title: {
          text: "Compare Sales Strategy",
          style: {
            fontWeight: 600,
          },
        },
        xaxis: {
          categories: [2008, 2009, 2010, 2011, 2012, 2013, 2014],
        },
        yaxis: {
          title: {
            text: undefined,
          },
        },
        tooltip: {
          shared: false,
          y: {
            formatter: function (val:any) {
              return val + "K";
            },
          },
        },
        fill: {
          type: "pattern",
          opacity: 1,
          pattern: {
            style: ["circles", "slantedLines", "verticalLines", "horizontalLines"], // string or array of strings
          },
        },
        states: {
          hover: {

          },
        },
        legend: {
          position: "right",
          offsetY: 40,
        },
        colors: colors,
      };
    }

  /**
 * Grouped Bar Chart
 */
  private _groupedBarChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.groupedBarChart = {
      series: [{
          data: [44, 55, 41, 64, 22, 43, 21],
        },
        {
          data: [53, 32, 33, 52, 13, 44, 32],
        },
      ],
      chart: {
        type: "bar",
        height: 410,
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
          dataLabels: {
            position: "top",
          },
        },
      },
      dataLabels: {
        enabled: true,
        offsetX: -6,
        style: {
          fontSize: "12px",
          colors: ["#fff"],
        },
      },
      stroke: {
        show: true,
        width: 1,
        colors: ["#fff"],
      },
      tooltip: {
        shared: true,
        intersect: false,
      },
      xaxis: {
        categories: [2001, 2002, 2003, 2004, 2005, 2006, 2007],
      },
      colors: colors,
    };
  }

  /**
 * Bar with Images
 */
   private _barWithImageChart(colors:any) {
    colors = this.getChartColorsArray(colors);
    this.barWithImageChart = {
      series: [{
        name: "coins",
        data: [
          2,
          4,
          3,
          4,
          3,
          5,
          5,
          6.5,
          6,
          5,
          4,
          5,
          8,
          7,
          7,
          8,
          8,
          10,
          9,
          9,
          12,
          12,
          11,
          12,
          13,
          14,
          16,
          14,
          15,
          17,
          19,
          21,
        ],
      }, ],
      chart: {
        type: "bar",
        height: 410,
        animations: {
          enabled: false,
        },
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
          barHeight: "100%",
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        colors: ["#fff"],
        width: 0.2,
      },
      labels: Array.apply(null).map(function (el, index) {
          return index + 1;
      }),
      yaxis: {
        axisBorder: {
          show: false,
        },
        axisTicks: {
          show: false,
        },
        labels: {
          show: false,
        },
        title: {
          text: "Weight",
        },
      },
      grid: {
        position: "back",
      },
      title: {
        text: "Paths filled by clipped image",
        align: "right",
        offsetY: 30,
        style: {
          fontWeight: 600,
        },
      },
      fill: {
        type: "image",
        opacity: .87,
        image: {
          src: ["assets/images/small/img-4.jpg"],
          width: 466,
          height: 406
        }
      },
      colors: colors
    };
   }

}
