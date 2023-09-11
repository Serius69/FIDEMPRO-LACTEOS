import { Component, OnInit } from '@angular/core';
import { circle, latLng, tileLayer } from 'leaflet';

import { TitleBox1Model, TitleBox2Model, TitleBox3Model, TitleBox4Model, otherWidgetsModel, widgetsActivitiesModel, widgetsTasksModel, TitleBox5Model, HotproductModel, BankModel, CandidateModel } from './widgets.model';
import { tileBoxs1, tileBoxs2, tileBoxs3, tileBoxs4, otherWidgets, widgetsActivities, widgetsTasks, tileBoxs5, hotproducts, candidate, bank } from './data';
import { UntypedFormBuilder, Validators, UntypedFormGroup, UntypedFormArray, AbstractControl } from '@angular/forms';

import { SwiperOptions } from 'swiper';

@Component({
  selector: 'app-widgets',
  templateUrl: './widgets.component.html',
  styleUrls: ['./widgets.component.scss']
})

/**
 * Widgets Component
 */
export class WidgetsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  tileBoxs1!: TitleBox1Model[];
  tileBoxs2!: TitleBox2Model[];
  tileBoxs3!: TitleBox3Model[];
  tileBoxs4!: TitleBox4Model[];
  tileBoxs5!: TitleBox5Model[];
  hotproducts!: HotproductModel[];
  candidates!: CandidateModel[];
  otherWidgets!: otherWidgetsModel[];
  widgetsActivities!: widgetsActivitiesModel[];
  widgetsTasks!: widgetsTasksModel[];
  bankcardlist!: BankModel[];
  basicBarChart: any;
  basicColumnChart: any;
  simpleDonutChart: any;
  basicHeatmapChart: any;
  ApplicationChart: any;
  InterviewedChart: any;
  HiredChart: any;
  candidatedetail: any;
  bankcards: any;

  cardForm!: UntypedFormGroup;

  // Form
  customcardData!: UntypedFormGroup;
  submitted = false;

  constructor(public formBuilder: UntypedFormBuilder) { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Velzon' },
      { label: 'Widgets', active: true }
    ];

    // Chat Data Get Function
    this._fetchData();

    // Chart Color Data Get Function
    this._basicBarChart('["--vz-info", "--vz-info", "--vz-info", "--vz-info", "--vz-danger", "--vz-info", "--vz-info", "--vz-info", "--vz-info", "--vz-info"]');
    this._basicColumnChart('["--vz-success", "--vz-light"]');
    this._simpleDonutChart('["--vz-primary", "--vz-info", "--vz-warning", "--vz-success"]');
    this._basicHeatmapChart('["--vz-info", "--vz-success", "--vz-primary", "--vz-warning", "--vz-danger"]');
    this._applicationChart('["--vz-success" , "--vz-transparent"]');
    this._interviewChart('["--vz-danger" , "--vz-transparent"]');
    this._hiredChart('["--vz-success", "--vz-transparent"]');

    // Validation
    this.customcardData = this.formBuilder.group({
      card_no: ['', [Validators.required]],
      cardholder: ['', [Validators.required]],
      month: ['', [Validators.required]],
      year: ['', [Validators.required]],
      cvc: ['', [Validators.required]]
    });

    /**
     * Form Validation
     */
    this.cardForm = this.formBuilder.group({
      ids: [''],
      amount: ['', [Validators.required]],
    });

  }

  /**
  * Returns form
  */
  get form() {
    return this.customcardData.controls;
  }

  setcardnumber(e: any) {
    var key = e.keyCode || e.charCode;
    var is_digit = key >= 48 && key <= 57 || key >= 96 && key <= 105;
    var is_delete = key == 8 || key == 46;
    if (is_digit || is_delete) {
      var text = e.target.value;
      (document.getElementById("card-num-elem") as HTMLElement).innerText = text
    }
  }

  setname(ev: any) {
    (document.getElementById("card-holder-elem") as HTMLElement).innerHTML = ev.target.value
  }

  setMonth(ev: any) {
    if (!ev.target.value) {
      (document.getElementById("expiry-month-elem") as HTMLElement).innerText = "00";
    } else {
      (document.getElementById("expiry-month-elem") as HTMLElement).innerText = ev.target.value;
    }
  }

  setYear(ev: any) {
    if (!ev.target.value) {
      (document.getElementById("expiry-year-elem") as HTMLElement).innerText = "00";
    } else {
      (document.getElementById("expiry-year-elem") as HTMLElement).innerText = ev.target.value;
    }
  }

  setCVC(ev: any) {
    (document.getElementById("cvc-elem") as HTMLElement).innerHTML = ev.target.value
  }

  custompay() {
    if (this.customcardData.valid) {
    }
    this.submitted = true;
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
 * Series Data
 */
  private generateData(count: number, yrange: { max: number; min: number; }) {
    var i = 0;
    var series = [];
    while (i < count) {
      var x = "w" + (i + 1).toString();
      var y =
        Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

      series.push({
        x: x,
        y: y
      });
      i++;
    }
    return series;
  }

  /**
 * Basic Bar Chart
 */
  private _basicBarChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.basicBarChart = {
      series: [{
        data: [1010, 1640, 490, 1255, 1050, 689, 800, 420, 1085, 589],
        name: 'Sessions',
      }],
      chart: {
        type: 'bar',
        height: 436,
        toolbar: {
          show: false,
        }
      },
      plotOptions: {
        bar: {
          borderRadius: 4,
          horizontal: true,
          distributed: true,
          dataLabels: {
            position: 'top',
          },
        }
      },
      dataLabels: {
        enabled: true,
        offsetX: 32,
        style: {
          fontSize: '12px',
          fontWeight: 400,
          colors: ['#adb5bd']
        }
      },
      colors: colors,
      legend: {
        show: false,
      },
      grid: {
        show: false,
      },
      xaxis: {
        categories: ['India', 'United States', 'China', 'Indonesia', 'Russia', 'Bangladesh', 'Canada', 'Brazil', 'Vietnam', 'UK'],
      },
    };
  }

  /**
  * Application Chart
  */
  private _applicationChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.ApplicationChart = {
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
 * Interviewed Chart
 */
  private _interviewChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.InterviewedChart = {
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
  * Hired Chart
  */
  private _hiredChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.HiredChart = {
      series: [{
        name: "Results",
        data: [0, 65, 103, 75, 120],
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
 * Basic Column Charts
 */
  private _basicColumnChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.basicColumnChart = {
      series: [{
        name: 'Last Year',
        data: [25.3, 12.5, 20.2, 18.5, 40.4, 25.4, 15.8, 22.3, 19.2, 25.3, 12.5, 20.2]
      }, {
        name: 'Current Year',
        data: [36.2, 22.4, 38.2, 30.5, 26.4, 30.4, 20.2, 29.6, 10.9, 36.2, 22.4, 38.2]
      }],
      chart: {
        type: 'bar',
        height: 306,
        stacked: true,
        toolbar: {
          show: false,
        }
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: '30%',
          borderRadius: 6,
        },
      },
      dataLabels: {
        enabled: false,
      },
      legend: {
        show: true,
        position: 'bottom',
        horizontalAlign: 'center',
        fontWeight: 400,
        fontSize: '8px',
        offsetX: 0,
        offsetY: 0,
        markers: {
          width: 9,
          height: 9,
          radius: 4,
        },
      },
      stroke: {
        show: true,
        width: 2,
        colors: ['transparent']
      },
      grid: {
        show: false,
      },
      colors: colors,
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        axisTicks: {
          show: false,
        },
        axisBorder: {
          show: true,
          offsetX: 0,
          offsetY: 0
        },
      },
      yaxis: {
        show: false
      },
      fill: {
        opacity: 1
      }
    };
  }

  /**
 * Simple Donut Chart
 */
  private _simpleDonutChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.simpleDonutChart = {
      series: [19405, 40552, 15824, 30635],
      labels: ["Bitcoin", "Ethereum", "Litecoin", "Dash"],
      chart: {
        type: "donut",
        height: 210,
      },
      plotOptions: {
        pie: {

          offsetX: 0,
          offsetY: 0,
          donut: {
            size: "70%",
            labels: {
              show: true,
              name: {
                show: true,
                fontSize: '18px',
                offsetY: -5,
              },
              value: {
                show: true,
                fontSize: '20px',
                color: '#343a40',
                fontWeight: 500,
                offsetY: 5,
                formatter: function (val: any) {
                  return "$" + val
                }
              },
              total: {
                show: true,
                fontSize: '13px',
                label: 'Total value',
                color: '#9599ad',
                fontWeight: 500,
              }
            }
          },
        },
      },
      dataLabels: {
        enabled: false,
      },
      legend: {
        show: false,
      },
      yaxis: {
        labels: {
          formatter: function (value: any) {
            return "$" + value;
          }
        }
      },
      stroke: {
        lineCap: "round",
        width: 2
      },
      colors: colors
    };
  }

  /**
 * Basic Heatmap Chart
 */
  private _basicHeatmapChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.basicHeatmapChart = {
      series: [{
        name: 'Jan',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'Feb',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'Mar',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'Apr',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'May',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'Jun',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'Jul',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'Aug',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      },
      {
        name: 'Sep',
        data: this.generateData(20, {
          min: -30,
          max: 55
        })
      }
      ],
      chart: {
        height: 310,
        type: 'heatmap',
        toolbar: {
          show: false
        }
      },
      legend: {
        show: false,
      },
      plotOptions: {
        heatmap: {
          shadeIntensity: 0.5,
          radius: 0,
          useFillColorAsStroke: true,
          colorScale: {
            ranges: [{
              from: -30,
              to: 5,
              name: 'Youtube',
              color: colors[0]
            },
            {
              from: 6,
              to: 20,
              name: 'Meta',
              color: colors[1]
            },
            {
              from: 21,
              to: 45,
              name: 'Google',
              color: colors[2]
            },
            {
              from: 46,
              to: 55,
              name: 'Medium',
              color: colors[3]
            },
            {
              from: 36,
              to: 40,
              name: 'Other',
              color: colors[4]
            }
            ]
          }
        }
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        width: 1
      },
      title: {
        style: {
          fontWeight: 500,
        },
      },
    };
  }

  // Chat Data Fetch
  private _fetchData() {
    this.tileBoxs1 = tileBoxs1;
    this.tileBoxs2 = tileBoxs2;
    this.tileBoxs3 = tileBoxs3;
    this.tileBoxs4 = tileBoxs4;
    this.tileBoxs5 = tileBoxs5;
    this.otherWidgets = otherWidgets;
    this.widgetsActivities = widgetsActivities;
    this.widgetsTasks = widgetsTasks;
    this.hotproducts = hotproducts;
    this.candidates = candidate;
    this.candidatedetail = this.candidates[0];
    this.bankcards = bank;
  }

  /**
   * Sale Location Map
   */
  options = {
    layers: [
      tileLayer("https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoidGhlbWVzYnJhbmQiLCJhIjoiY2xmbmc3bTV4MGw1ejNzbnJqOWpubzhnciJ9.DNkdZVKLnQ6I9NOz7EED-w", {
        id: "mapbox/light-v9",
        tileSize: 512,
        zoomOffset: -1,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
      })
    ],
    zoom: 1.1,
    center: latLng(28, 1.5)
  };
  layers = [
    circle([41.9, 12.45], { color: "#435fe3", opacity: 0.5, weight: 10, fillColor: "#435fe3", fillOpacity: 1, radius: 400000, }),
    circle([12.05, -61.75], { color: "#435fe3", opacity: 0.5, weight: 10, fillColor: "#435fe3", fillOpacity: 1, radius: 400000, }),
    circle([1.3, 103.8], { color: "#435fe3", opacity: 0.5, weight: 10, fillColor: "#435fe3", fillOpacity: 1, radius: 400000, }),
  ];

  /**
     * Swiper Responsive setting
     */
  public Responsive: SwiperOptions = {
    // navigation: true,
    spaceBetween: 25,
    breakpoints: {
      768: {
        slidesPerView: 2,
      },
      1200: {
        slidesPerView: 1.5,
      }
    }
  };

  // open Candidate Detail
  opendetail(id: any) {
    this.candidatedetail = this.candidates[id]
  }

  // select bank
  confirmcard() {
    if (this.cardForm.valid) {
      document.getElementById('notification-warn')?.classList.add('d-none')
      const amount = this.cardForm.get('amount')?.value;
      (document.getElementById("notification-overlay") as HTMLElement).style.visibility = "visible";
      (document.getElementById("notification-overlay") as HTMLElement).style.opacity = "1";
      (document.querySelector("#notification-overlay .success-pay") as HTMLElement).innerHTML = amount + ' Payment Successfully'
    } else {
      document.getElementById('notification-warn')?.classList.remove('d-none')
    }
  }

  backtohome() {
    (document.getElementById("notification-overlay") as HTMLElement).style.visibility = "hidden";
    (document.getElementById("notification-overlay") as HTMLElement).style.opacity = "0";
  }

}
