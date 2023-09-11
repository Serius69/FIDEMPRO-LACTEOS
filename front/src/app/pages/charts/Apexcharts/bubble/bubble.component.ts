import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-bubble',
  templateUrl: './bubble.component.html',
  styleUrls: ['./bubble.component.scss']
})

/**
 * Apex Bubble Component
 */
export class BubbleComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  simpleBubbleChart: any;
  BubbleChart: any;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Bubble Charts', active: true }
    ];

    // Chart Color Data Get Function
    this._simpleBubbleChart('["--vz-primary", "--vz-info", "--vz-warning", "--vz-success"]');
    this._BubbleChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger"]');

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
 * Series data
 */
private generateData(baseval: number, count: number, yrange: { max: number; min: number; }) {
  var i = 0;
  var series = [];
  while (i < count) {
      var x = Math.floor(Math.random() * (750 - 1 + 1)) + 1;
      var y =
          Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;
      var z = Math.floor(Math.random() * (75 - 15 + 1)) + 15;

      series.push([x, y, z]);
      baseval += 86400000;
      i++;
  }
  return series;
}

  /**
 * Simple Bubble Chart
 */
  private _simpleBubbleChart(colors:any) {
    colors = this.getChartColorsArray(colors);    
    this.simpleBubbleChart = {
      series: [
        {
          name: "Bubble1",
          data: this.generateData(new Date("11 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
        {
          name: "Bubble2",
          data: this.generateData(new Date("12 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
        {
          name: "Bubble3",
          data: this.generateData(new Date("13 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
        {
          name: "Bubble4",
          data: this.generateData(new Date("14 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
      ],
      chart: {
        height: 350,
        type: "bubble",
        toolbar: {
          show: false,
        },
      },
      dataLabels: {
        enabled: false,
      },
      fill: {
        opacity: 0.8,
      },
      title: {
        text: "Simple Bubble Chart",
        style: {
          fontWeight: 500,
        },
      },
      xaxis: {
        tickAmount: 12,
        type: "category",
      },
      yaxis: {
        max: 70,
      },
      colors: colors,
    }
  }

  /**
 * 3D Bubble Chart
 */
   private _BubbleChart(colors:any) {
    colors = this.getChartColorsArray(colors);  
    this.BubbleChart = {
      series: [
        {
          name: "Product1",
          data: this.generateData(new Date("11 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
        {
          name: "Product2",
          data: this.generateData(new Date("11 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
        {
          name: "Product3",
          data: this.generateData(new Date("11 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
        {
          name: "Product4",
          data: this.generateData(new Date("11 Feb 2017 GMT").getTime(), 20, {
            min: 10,
            max: 60,
          }),
        },
      ],
        chart: {
          height: 350,
          type: "bubble",
          toolbar: {
            show: false,
          },
        },
        dataLabels: {
          enabled: false,
        },
        fill: {
          type: "gradient",
        },
        title: {
          text: "3D Bubble Chart",
          style: {
            fontWeight: 500,
          },
        },
        xaxis: {
          tickAmount: 12,
          type: "datetime",
          labels: {
            rotate: 0,
          },
        },
        yaxis: {
          max: 70,
        },
        theme: {
          palette: "palette2",
        },
        colors: colors,
    };
   }

}
