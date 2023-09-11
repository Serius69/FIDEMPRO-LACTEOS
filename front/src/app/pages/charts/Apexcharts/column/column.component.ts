import { Component, OnInit } from '@angular/core';

import { arrayData } from "./data";


@Component({
  selector: 'app-column',
  templateUrl: './column.component.html',
  styleUrls: ['./column.component.scss']
})

/**
 * Apex Column Component
 */
export class ColumnComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  basicChart: any;
  columnWithDataChart: any;
  StackedColumnChart: any;
  StackedColumn100Chart: any;
  ColumnWithMarkerChart: any;
  ColumnWithRotatedChart: any;
  ColumnWithNagetiveChart: any;
  rangeColumnChart: any;
  dynamicLoadedChart: any;
  dynamicQuarterLoadedChart: any;
  distributedColumnChart: any;
  groupLabelChart: any;
  groupedstackedcolumns: any;
  dumbbellchart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Area Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._basicChart('["--vz-danger", "--vz-primary", "--vz-success"]');
    this._columnWithDataChart('["--vz-success"]');
    this._StackedColumnChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger"]');
    this._StackedColumn100Chart('["--vz-primary", "--vz-success", "--vz-warning"]');
    this._ColumnWithMarkerChart('["--vz-success", "--vz-primary"]');
    this._ColumnWithRotatedChart('["--vz-info"]');
    this._ColumnWithNagetiveChart('["--vz-success", "--vz-danger", "--vz-warning"]');
    this._rangeColumnChart('["--vz-primary", "--vz-success"]');
    this._dynamicQuarterLoadedChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-body-color", "--vz-info"]');
    this._dynamicLoadedChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-body-color", "--vz-info"]');
    this._distributedColumnChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-body-color", "--vz-info"]')
    this._groupLabelChart('["--vz-info"]')
    this._groupedstackedcolumns('["--vz-success", "--vz-primary","--vz-secondary", "--vz-danger"]')
    this._dumbbellchart('["--vz-success", "--vz-primary"]')
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
 * Basic Column Charts
 */
  private _basicChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.basicChart = {
      series: [{
        name: "Net Profit",
        data: [46, 57, 59, 54, 62, 58, 64, 60, 66],
      },
      {
        name: "Revenue",
        data: [74, 83, 102, 97, 86, 106, 93, 114, 94],
      },
      {
        name: "Free Cash Flow",
        data: [37, 42, 38, 26, 47, 50, 54, 55, 43],
      },
      ],
      chart: {
        height: 350,
        type: "bar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: "45%",
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        show: true,
        width: 2,
        colors: ["transparent"],
      },
      colors: colors,
      xaxis: {
        categories: [
          "Feb",
          "Mar",
          "Apr",
          "May",
          "Jun",
          "Jul",
          "Aug",
          "Sep",
          "Oct",
        ],
      },
      yaxis: {
        title: {
          text: "$ (thousands)",
        },
      },
      grid: {
        borderColor: "#f1f1f1",
      },
      fill: {
        opacity: 1,
      },
      tooltip: {
        y: {
          formatter: function (val: any) {
            return "$ " + val + " thousands";
          },
        },
      },
    };
  }

  /**
 * Column with Data Labels
 */
  private _columnWithDataChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.columnWithDataChart = {
      series: [{
        name: "Inflation",
        data: [2.5, 3.2, 5.0, 10.1, 4.2, 3.8, 3, 2.4, 4.0, 1.2, 3.5, 0.8],
      },],
      chart: {
        height: 350,
        type: "bar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          dataLabels: {
            position: "top", // top, center, bottom
          },
        },
      },
      dataLabels: {
        enabled: true,
        formatter: function (val: any) {
          return val + "%";
        },
        offsetY: -20,
        style: {
          fontSize: "12px",
          colors: ["#adb5bd"],
        },
      },
      colors: colors,
      grid: {
        borderColor: "#f1f1f1",
      },
      xaxis: {
        categories: [
          "Jan",
          "Feb",
          "Mar",
          "Apr",
          "May",
          "Jun",
          "Jul",
          "Aug",
          "Sep",
          "Oct",
          "Nov",
          "Dec",
        ],
        position: "top",
        labels: {
          offsetY: -18,
        },
        axisBorder: {
          show: false,
        },
        axisTicks: {
          show: false,
        },
        crosshairs: {
          fill: {
            type: "gradient",
            gradient: {
              colorFrom: "#D8E3F0",
              colorTo: "#BED1E6",
              stops: [0, 100],
              opacityFrom: 0.4,
              opacityTo: 0.5,
            },
          },
        },
        tooltip: {
          enabled: true,
          offsetY: -35,
        },
      },
      fill: {
        gradient: {
          shade: "light",
          type: "horizontal",
          shadeIntensity: 0.25,
          gradientToColors: undefined,
          inverseColors: true,
          opacityFrom: 1,
          opacityTo: 1,
          stops: [50, 0, 100, 100],
        },
      },
      yaxis: {
        axisBorder: {
          show: false,
        },
        axisTicks: {
          show: false,
        },
        labels: {
          show: false,
          formatter: function (val: any) {
            return val + "%";
          },
        },
      },
      title: {
        text: "Monthly Inflation in Argentina, 2002",
        floating: true,
        offsetY: 320,
        align: "center",
        style: {
          color: "#444",
          fontWeight: 500,
        },
      },
    };
  }

  /**
 * Stacked Column Charts
 */
  private _StackedColumnChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.StackedColumnChart = {
      series: [{
        name: "PRODUCT A",
        data: [44, 55, 41, 67, 22, 43],
      },
      {
        name: "PRODUCT B",
        data: [13, 23, 20, 8, 13, 27],
      },
      {
        name: "PRODUCT C",
        data: [11, 17, 15, 15, 21, 14],
      },
      {
        name: "PRODUCT D",
        data: [21, 7, 25, 13, 22, 8],
      },
      ],
      chart: {
        type: "bar",
        height: 350,
        stacked: true,
        toolbar: {
          show: false,
        },
        zoom: {
          enabled: true,
        },
      },
      responsive: [{
        breakpoint: 480,
        options: {
          legend: {
            position: "bottom",
            offsetX: -10,
            offsetY: 0,
          },
        },
      },],
      plotOptions: {
        bar: {
          horizontal: false,
          borderRadius: 10,
        },
      },
      xaxis: {
        type: "datetime",
        categories: [
          "01/01/2011 GMT",
          "01/02/2011 GMT",
          "01/03/2011 GMT",
          "01/04/2011 GMT",
          "01/05/2011 GMT",
          "01/06/2011 GMT",
        ],
      },
      legend: {
        position: "right",
        offsetY: 40,
      },
      fill: {
        opacity: 1,
      },
      colors: colors,
    };
  }

  /**
* Stacked Column 100
*/
  private _StackedColumn100Chart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.StackedColumn100Chart = {
      series: [{
        name: "PRODUCT A",
        data: [44, 55, 41, 67, 22, 43, 21, 49],
      },
      {
        name: "PRODUCT B",
        data: [13, 23, 20, 8, 13, 27, 33, 12],
      },
      {
        name: "PRODUCT C",
        data: [11, 17, 15, 15, 21, 14, 15, 13],
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
      responsive: [{
        breakpoint: 480,
        options: {
          legend: {
            position: "bottom",
            offsetX: -10,
            offsetY: 0,
          },
        },
      },],
      xaxis: {
        categories: [
          "2011 Q1",
          "2011 Q2",
          "2011 Q3",
          "2011 Q4",
          "2012 Q1",
          "2012 Q2",
          "2012 Q3",
          "2012 Q4",
        ],
      },
      fill: {
        opacity: 1,
      },
      legend: {
        position: "right",
        offsetX: 0,
        offsetY: 50,
      },
      colors: colors,
    };
  }

  /**
 * Column with Markers
 */
  private _ColumnWithMarkerChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.ColumnWithMarkerChart = {
      series: [{
        name: "Actual",
        data: [{
          x: "2011",
          y: 1292,
          goals: [{
            name: "Expected",
            value: 1400,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        {
          x: "2012",
          y: 4432,
          goals: [{
            name: "Expected",
            value: 5400,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        {
          x: "2013",
          y: 5423,
          goals: [{
            name: "Expected",
            value: 5200,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        {
          x: "2014",
          y: 6653,
          goals: [{
            name: "Expected",
            value: 6500,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        {
          x: "2015",
          y: 8133,
          goals: [{
            name: "Expected",
            value: 6600,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        {
          x: "2016",
          y: 7132,
          goals: [{
            name: "Expected",
            value: 7500,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        {
          x: "2017",
          y: 7332,
          goals: [{
            name: "Expected",
            value: 8700,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        {
          x: "2018",
          y: 6553,
          goals: [{
            name: "Expected",
            value: 7300,
            strokeWidth: 5,
            strokeColor: "#775DD0",
          },],
        },
        ],
      },],
      chart: {
        height: 350,
        type: "bar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          columnWidth: "30%",
        },
      },
      colors: colors,
      dataLabels: {
        enabled: false,
      },
      legend: {
        show: true,
        showForSingleSeries: true,
        customLegendItems: ["Actual", "Expected"],
        markers: {
          fillColors: ["#63ad6f", "#564ab1"],
        },
      },
    };
  }

  /**
* Column with Rotated Labels
*/
  private _ColumnWithRotatedChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.ColumnWithRotatedChart = {
      series: [{
        name: "Servings",
        data: [44, 55, 41, 67, 22, 43, 21, 33, 45, 31, 87, 65, 35],
      },],
      annotations: {
        points: [{
          x: "Bananas",
          seriesIndex: 0,
          label: {
            borderColor: "#775DD0",
            offsetY: 0,
            style: {
              color: "#fff",
              background: "#775DD0",
            },
            text: "Bananas are good",
          },
        },],
      },
      chart: {
        height: 350,
        type: "bar",
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          borderRadius: 10,
          columnWidth: "50%",
        },
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        width: 2,
      },
      xaxis: {
        labels: {
          rotate: -45,
        },
        categories: [
          "Apples",
          "Oranges",
          "Strawberries",
          "Pineapples",
          "Mangoes",
          "Bananas",
          "Blackberries",
          "Pears",
          "Watermelons",
          "Cherries",
          "Pomegranates",
          "Tangerines",
          "Papayas",
        ],
        tickPlacement: "on",
      },
      yaxis: {
        title: {
          text: "Servings",
        },
      },
      fill: {
        type: "gradient",
        gradient: {
          shade: "light",
          type: "horizontal",
          shadeIntensity: 0.25,
          gradientToColors: undefined,
          inverseColors: true,
          opacityFrom: 0.85,
          opacityTo: 0.85,
          stops: [50, 0, 100],
        },
      },
      colors: colors
    };
  }

  /**
* Column with Nagetive Values
*/
  private _ColumnWithNagetiveChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.ColumnWithNagetiveChart = {
      series: [{
        name: "Cash Flow",
        data: [
          1.45,
          5.42,
          5.9,
          -0.42,
          -12.6,
          -18.1,
          -18.2,
          -14.16,
          -11.1,
          -6.09,
          0.34,
          3.88,
          13.07,
          5.8,
          2,
          7.37,
          8.1,
          13.57,
          15.75,
          17.1,
          19.8,
          -27.03,
          -54.4,
          -47.2,
          -43.3,
          -18.6,
          -48.6,
          -41.1,
          -39.6,
          -37.6,
          -29.4,
          -21.4,
          -2.4,
        ],
      },],
      chart: {
        type: "bar",
        height: 350,
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          colors: {
            ranges: [{
              from: -100,
              to: -46,
              color: "#f56e6e",
            },
            {
              from: -45,
              to: 0,
              color: "#f7cc53",
            },
            ],
          },
          columnWidth: "80%",
        },
      },
      dataLabels: {
        enabled: false,
      },
      yaxis: {
        title: {
          text: "Growth",
        },
        labels: {
          formatter: function (y: any) {
            return y.toFixed(0) + "%";
          },
        },
      },
      xaxis: {
        type: "datetime",
        categories: [
          "2011-01-01",
          "2011-02-01",
          "2011-03-01",
          "2011-04-01",
          "2011-05-01",
          "2011-06-01",
          "2011-07-01",
          "2011-08-01",
          "2011-09-01",
          "2011-10-01",
          "2011-11-01",
          "2011-12-01",
          "2012-01-01",
          "2012-02-01",
          "2012-03-01",
          "2012-04-01",
          "2012-05-01",
          "2012-06-01",
          "2012-07-01",
          "2012-08-01",
          "2012-09-01",
          "2012-10-01",
          "2012-11-01",
          "2012-12-01",
          "2013-01-01",
          "2013-02-01",
          "2013-03-01",
          "2013-04-01",
          "2013-05-01",
          "2013-06-01",
          "2013-07-01",
          "2013-08-01",
          "2013-09-01",
        ],
        labels: {
          rotate: -90,
        },
      },
    };
  }

  /**
 * Range Column Chart
 */
  private _rangeColumnChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.rangeColumnChart = {
      series: [{
        data: [{
          x: "Team A",
          y: [1, 5],
        },
        {
          x: "Team B",
          y: [4, 6],
        },
        {
          x: "Team C",
          y: [5, 8],
        },
        {
          x: "Team D",
          y: [3, 11],
        },
        ],
      },
      {
        data: [{
          x: "Team A",
          y: [2, 6],
        },
        {
          x: "Team B",
          y: [1, 3],
        },
        {
          x: "Team C",
          y: [7, 8],
        },
        {
          x: "Team D",
          y: [5, 9],
        },
        ],
      },
      ],
      chart: {
        type: "rangeBar",
        height: 335,
        toolbar: {
          show: false,
        },
      },
      plotOptions: {
        bar: {
          horizontal: false,
        },
      },
      dataLabels: {
        enabled: true,
      },
      legend: {
        show: false,
      },
      colors: colors,
    };
  }

  /**
 * Dynamin Loaded Chart
 */
  private shuffleArray(array: any) {
    for (var i = array.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = array[i];
      array[i] = array[j];
      array[j] = temp;
    }
    return array;
  }

  private updateQuarterChart(sourceChart: any, destChartIDToUpdate: any) {
    var series = [];
    var seriesIndex = 0;
    var colors = [];

    if (sourceChart.w.globals.selectedDataPoints[0]) {
      var selectedPoints = sourceChart.w.globals.selectedDataPoints;
      for (var i = 0; i < selectedPoints[seriesIndex].length; i++) {
        var selectedIndex = selectedPoints[seriesIndex][i];
        var yearSeries = sourceChart.w.config.series[seriesIndex];
        series.push({
          name: yearSeries.data[selectedIndex].x,
          data: yearSeries.data[selectedIndex].quarters
        });
        colors.push(yearSeries.data[selectedIndex].color);
      }

      if (series.length === 0)
        series = [
          {
            data: []
          }
        ];

      return window.ApexCharts.exec(destChartIDToUpdate, "updateOptions", {
        series: series,
        colors: colors,
        fill: {
          colors: colors
        }
      });
    }
  }

  private _dynamicLoadedChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    var dataSet = this.shuffleArray(arrayData);
    this.dynamicLoadedChart = {
      series: [{
        name: "year",
        data: [
          {
            x: "2011",
            y: dataSet[0].y,
            color: colors[0],
            quarters: dataSet[0].quarters
          },
          {
            x: "2012",
            y: dataSet[1].y,
            color: colors[1],
            quarters: dataSet[1].quarters
          },
          {
            x: "2013",
            y: dataSet[2].y,
            color: colors[2],
            quarters: dataSet[2].quarters
          },
          {
            x: "2014",
            y: dataSet[3].y,
            color: colors[3],
            quarters: dataSet[3].quarters
          },
          {
            x: "2015",
            y: dataSet[4].y,
            color: colors[4],
            quarters: dataSet[4].quarters
          },
          {
            x: "2016",
            y: dataSet[5].y,
            color: colors[5],
            quarters: dataSet[5].quarters
          }
        ],
      },],
      chart: {
        id: "barYear",
        height: 400,
        width: "100%",
        type: "bar",
        events: {
          dataPointSelection: (e: any, chart: any, opts: any) => {
            var quarterChartEl = document.querySelector("#chart-quarter");
            var yearChartEl = document.querySelector("#chart-year");

            if (opts.selectedDataPoints[0].length === 1) {
              if (quarterChartEl!.classList.contains("active")) {
                this.updateQuarterChart(chart, "barQuarter");
              } else {
                yearChartEl!.classList.add("chart-quarter-activated");
                quarterChartEl!.classList.add("active");
                this.updateQuarterChart(chart, "barQuarter");
              }
            } else {
              this.updateQuarterChart(chart, "barQuarter");
            }

            if (opts.selectedDataPoints[0].length === 0) {
              yearChartEl!.classList.remove("chart-quarter-activated");
              quarterChartEl!.classList.remove("active");
            }
          },
          updated: (chart: any) => {
            this.updateQuarterChart(chart, "barQuarter");
          }
        }
      },
      plotOptions: {
        bar: {
          distributed: true,
          horizontal: true,
          barHeight: "75%",
          dataLabels: {
            position: "bottom",
          },
        },
      },
      dataLabels: {
        enabled: true,
        textAnchor: "start",
        style: {
          colors: ["#fff"],
        },
        formatter: function (val: any, opt: any) {
          return opt.w.globals.labels[opt.dataPointIndex];
        },
        offsetX: 0,
        dropShadow: {
          enabled: true,
        },
      },
      colors: colors,
      states: {
        normal: {
          filter: {
            type: "desaturate",
          },
        },
        active: {
          allowMultipleDataPointsSelection: true,
          filter: {
            type: "darken",
            value: 1,
          },
        },
      },
      tooltip: {
        x: {
          show: false,
        },
      },
      title: {
        text: "Yearly Results",
        offsetX: 15,
      },
      subtitle: {
        text: "(Click on bar to see details)",
        offsetX: 15,
      },
      yaxis: {
        labels: {
          show: false,
        },
      },
      legend: {
        show: false
      }
    };
  }

  /**
 * Dynamin Quarter Loaded Chart
 */
  private _dynamicQuarterLoadedChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.dynamicQuarterLoadedChart = {
      series: [
        {
          name: "quarter",
          data: []
        }
      ],
      chart: {
        id: "barQuarter",
        height: 400,
        width: "100%",
        type: "bar",
        stacked: true
      },
      plotOptions: {
        bar: {
          columnWidth: "50%",
          horizontal: false
        }
      },
      legend: {
        show: false
      },
      grid: {
        yaxis: {
          lines: {
            show: false
          }
        },
        xaxis: {
          lines: {
            show: true
          }
        }
      },
      yaxis: {
        labels: {
          show: false
        }
      },
      title: {
        text: "Quarterly Results",
        offsetX: 10
      },
      tooltip: {
        x: {
          formatter: function (val: any, opts: any) {
            return opts.w.globals.seriesNames[opts.seriesIndex];
          }
        }
      },
      colors: colors,
    };
  }

  /**
 * Distributed Columns Charts
   */
  private _distributedColumnChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.distributedColumnChart = {
      series: [{
        data: [21, 22, 10, 28, 16, 21, 13, 30]
      }],
      chart: {
        height: 350,
        type: 'bar',
        events: {
          click: function (chart: any, w: any, e: any) {
          }
        }
      },
      colors: colors,
      plotOptions: {
        bar: {
          columnWidth: '45%',
          distributed: true,
        }
      },
      dataLabels: {
        enabled: false
      },
      legend: {
        show: false
      },
      xaxis: {
        categories: [
          ['John', 'Doe'],
          ['Joe', 'Smith'],
          ['Jake', 'Williams'],
          'Amber',
          ['Peter', 'Brown'],
          ['Mary', 'Evans'],
          ['David', 'Wilson'],
          ['Lily', 'Roberts'],
        ],
        labels: {
          style: {
            colors: colors,
            fontSize: '12px'
          }
        }
      }
    };
  }

  /**
  * Column with Group Label Charts
  */
  private _groupLabelChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.groupLabelChart = {
      series: [{
        name: "sales",
        data: [{
          x: '2020/01/01',
          y: 400
        }, {
          x: '2020/04/01',
          y: 430
        }, {
          x: '2020/07/01',
          y: 448
        }, {
          x: '2020/10/01',
          y: 470
        }, {
          x: '2021/01/01',
          y: 540
        }, {
          x: '2021/04/01',
          y: 580
        }, {
          x: '2021/07/01',
          y: 690
        }, {
          x: '2021/10/01',
          y: 690
        }]
      }],
      chart: {
        type: 'bar',
        height: 350,
        toolbar: {
          show: false,
        }
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: '45%',
        },
      },
      colors: colors,
      xaxis: {
        type: 'category',
        categories: ['Q1', 'Q2', 'Q3', 'Q4', 'Q1', 'Q2', 'Q3', 'Q4'],
        group: {
          style: {
            fontSize: '10px',
            fontWeight: 700
          },
          groups: [
            { title: '2020', cols: 4 },
            { title: '2021', cols: 4 }
          ]
        }
      },
      title: {
        text: 'Grouped Labels on the X-axis',
        style: {
          fontWeight: 500,
        },
      },
      tooltip: {
        categories: ['Q1', 'Q2', 'Q3', 'Q4', 'Q1', 'Q2', 'Q3', 'Q4'],
      },
    };
  }


  /**
* Grouped stacked columns
*/
  private _groupedstackedcolumns(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.groupedstackedcolumns = {
      series: [
        {
          name: 'Q1 Budget',
          group: 'budget',
          data: [44000, 55000, 41000, 67000, 22000, 43000]
        },
        {
          name: 'Q1 Actual',
          group: 'actual',
          data: [48000, 50000, 40000, 65000, 25000, 40000]
        },
        {
          name: 'Q2 Budget',
          group: 'budget',
          data: [13000, 36000, 20000, 8000, 13000, 27000]
        },
        {
          name: 'Q2 Actual',
          group: 'actual',
          data: [20000, 40000, 25000, 10000, 12000, 28000]
        }
      ],
      chart: {
        type: 'bar',
        height: 350,
        stacked: true,
      },
      stroke: {
        width: 1,
        colors: ['#fff']
      },

      plotOptions: {
        bar: {
          horizontal: false
        }
      },
      xaxis: {
        categories: [
          'Online advertising',
          'Sales Training',
          'Print advertising',
          'Catalogs',
          'Meetings',
          'Public relations'
        ]
      },
      fill: {
        opacity: 1
      },
      colors: colors,

      legend: {
        position: 'top',
        horizontalAlign: 'left'
      }
    };
  }

  /**
* dumbbellchart columns
*/
  private _dumbbellchart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.dumbbellchart = {
      series: [
        {
          data: [
            {
              x: '2008',
              y: [2800, 4500]
            },
            {
              x: '2009',
              y: [3200, 4100]
            },
            {
              x: '2010',
              y: [2950, 7800]
            },
            {
              x: '2011',
              y: [3000, 4600]
            },
            {
              x: '2012',
              y: [3500, 4100]
            },
            {
              x: '2013',
              y: [4500, 6500]
            },
            {
              x: '2014',
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
      plotOptions: {
        bar: {
          isDumbbell: true,
          columnWidth: 3,
          dumbbellColors: colors
        }
      },
      legend: {
        show: true,
        showForSingleSeries: true,
        position: 'top',
        horizontalAlign: 'left',
        customLegendItems: ['Product A', 'Product B']
      },
      fill: {
        type: 'gradient',
        gradient: {
          type: 'vertical',
          gradientToColors: ['#00E396'],
          inverseColors: true,
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
      },
      xaxis: {
        tickPlacement: 'on'
      }
    };
  }

}
