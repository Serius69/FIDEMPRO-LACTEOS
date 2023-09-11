import { Component } from '@angular/core';

@Component({
  selector: 'app-funnel',
  templateUrl: './funnel.component.html',
  styleUrls: ['./funnel.component.scss']
})
export class FunnelComponent {
  // bread crumb items
  breadCrumbItems!: Array<{}>;
  Funnel: any
  Pyramid: any

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Apexcharts' },
      { label: 'Funnel Charts', active: true }
    ];
    this._Funnel('["--vz-success "]');
    this._Pyramid('["--vz-info", "--vz-danger", "--vz-primary", "--vz-secondary", "--vz-success", "--vz-body-color", "--vz-warning"]')
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
 * Basic _Funnel Chart
 */
  private _Funnel(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.Funnel = {
      series: [
        {
          name: "Funnel Series",
          data: [1380, 1100, 990, 880, 740, 548, 330, 200]
        }
      ],
      chart: {
        type: "bar",
        height: 350
      },
      plotOptions: {
        bar: {
          borderRadius: 0,
          horizontal: true,
          barHeight: "80%",
          isFunnel: true
        }
      },
      colors: colors,
      dataLabels: {
        enabled: true,
        formatter: function (val: any, opt: any) {
          return opt.w.globals.labels[opt.dataPointIndex] + ":  " + val;
        },
        dropShadow: {
          enabled: true
        }
      },
      title: {
        text: "Recruitment Funnel",
        align: "center"
      },
      xaxis: {
        categories: [
          "Sourced",
          "Screened",
          "Assessed",
          "HR Interview",
          "Technical",
          "Verify",
          "Offered",
          "Hired"
        ]
      },
      legend: {
        show: false
      }
    };

  }
  /**
 * Basic Heatmap Chart
 */
  private _Pyramid(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.Pyramid = {
      series: [
        {
          name: "",
          data: [200, 330, 548, 740, 880, 990, 1100, 1380]
        }
      ],
      chart: {
        type: "bar",
        height: 350
      },
      plotOptions: {
        bar: {
          borderRadius: 0,
          horizontal: true,
          distributed: true,
          barHeight: "80%",
          isFunnel: true
        }
      },
      colors:
        colors
      ,
      dataLabels: {
        enabled: true,
        formatter: function (val: any, opt: any) {
          return opt.w.globals.labels[opt.dataPointIndex];
        },
        dropShadow: {
          enabled: true
        }
      },
      title: {
        text: "Pyramid Chart",
        align: "center"
      },
      xaxis: {
        categories: [
          "Sweets",
          "Processed Foods",
          "Healthy Fats",
          "Meat",
          "Beans & Legumes",
          "Dairy",
          "Fruits & Vegetables",
          "Grains"
        ]
      },
      legend: {
        show: false
      }
    };
  }
}
