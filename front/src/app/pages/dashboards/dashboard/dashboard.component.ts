import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { ToastService } from './toast-service';

import { circle, latLng, tileLayer } from 'leaflet';
import { SwiperOptions } from 'swiper';

import { BestSelling, TopSelling, Recentelling, statData } from './data';
import { ChartType } from './dashboard.model';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})

/**
 * Ecommerce Component
 */
export class DashboardComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  analyticsChart!: ChartType;
  BestSelling: any;
  TopSelling: any;
  Recentelling: any;
  SalesCategoryChart!: ChartType;
  statData!: any;
  currentDate: any;
  // Current Date
  // currentDate: Date = new Date();

  constructor(public toastService: ToastService) {
    var date = new Date();
    var firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
    var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    this.currentDate = { from: firstDay, to: lastDay }
  }

  ngOnInit(): void {
    /**
     * BreadCrumb
     */
    this.breadCrumbItems = [
      { label: 'Dashboards' },
      { label: 'Dashboard', active: true }
    ];

    if (localStorage.getItem('toast')) {
      this.toastService.show('Logged in Successfull.', { classname: 'bg-success text-center text-white', delay: 5000 });
      localStorage.removeItem('toast');
    }

    /**
    * Fetches the data
    */
    this.fetchData();

    // Chart Color Data Get Function
    this._analyticsChart('["--vz-primary", "--vz-success", "--vz-danger"]');
    this._SalesCategoryChart('["--vz-primary", "--vz-success", "--vz-warning", "--vz-danger", "--vz-info"]');
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
 * Sales Analytics Chart
 */
  setrevenuevalue(value: any) {
    if (value == 'all') {
      this.analyticsChart.series = [{
        name: 'Orders',
        type: 'area',
        data: [34, 65, 46, 68, 49, 61, 42, 44, 78, 52, 63, 67]
      }, {
        name: 'Earnings',
        type: 'bar',
        data: [89.25, 98.58, 68.74, 108.87, 77.54, 84.03, 51.24, 28.57, 92.57, 42.36, 88.51, 36.57]
      }, {
        name: 'Refunds',
        type: 'line',
        data: [8, 12, 7, 17, 21, 11, 5, 9, 7, 29, 12, 35]
      }]
    }
    if (value == '1M') {
      this.analyticsChart.series = [{
        name: 'Orders',
        type: 'area',
        data: [24, 75, 16, 98, 19, 41, 52, 34, 28, 52, 63, 67]
      }, {
        name: 'Earnings',
        type: 'bar',
        data: [99.25, 28.58, 98.74, 12.87, 107.54, 94.03, 11.24, 48.57, 22.57, 42.36, 88.51, 36.57]
      }, {
        name: 'Refunds',
        type: 'line',
        data: [28, 22, 17, 27, 21, 11, 5, 9, 17, 29, 12, 15]
      }]
    }
    if (value == '6M') {
      this.analyticsChart.series = [{
        name: 'Orders',
        type: 'area',
        data: [34, 75, 66, 78, 29, 41, 32, 44, 58, 52, 43, 77]
      }, {
        name: 'Earnings',
        type: 'bar',
        data: [109.25, 48.58, 38.74, 57.87, 77.54, 84.03, 31.24, 18.57, 92.57, 42.36, 48.51, 56.57]
      }, {
        name: 'Refunds',
        type: 'line',
        data: [12, 22, 17, 27, 1, 51, 5, 9, 7, 29, 12, 35]
      }]
    }
    if (value == '1Y') {
      this.analyticsChart.series = [{
        name: 'Orders',
        type: 'area',
        data: [34, 65, 46, 68, 49, 61, 42, 44, 78, 52, 63, 67]
      }, {
        name: 'Earnings',
        type: 'bar',
        data: [89.25, 98.58, 68.74, 108.87, 77.54, 84.03, 51.24, 28.57, 92.57, 42.36, 88.51, 36.57]
      }, {
        name: 'Refunds',
        type: 'line',
        data: [8, 12, 7, 17, 21, 11, 5, 9, 7, 29, 12, 35]
      }]
    }
  }

  private _analyticsChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.analyticsChart = {
      chart: {
        height: 370,
        type: "line",
        toolbar: {
          show: false,
        },
        style:{
          direction:'rtl'
        }
      },
      stroke: {
        curve: "straight",
        dashArray: [0, 0, 8],
        width: [2, 0, 2.2],
      },
      colors: colors,
      series: [{
        name: 'Orders',
        type: 'area',
        data: [34, 65, 46, 68, 49, 61, 42, 44, 78, 52, 63, 67]
      }, {
        name: 'Earnings',
        type: 'bar',
        data: [89.25, 98.58, 68.74, 108.87, 77.54, 84.03, 51.24, 28.57, 92.57, 42.36,
          88.51, 36.57]
      }, {
        name: 'Refunds',
        type: 'line',
        data: [8, 12, 7, 17, 21, 11, 5, 9, 7, 29, 12, 35]
      }],
      fill: {
        opacity: [0.1, 0.9, 1],
      },
      labels: ['01/01/2003', '02/01/2003', '03/01/2003', '04/01/2003', '05/01/2003', '06/01/2003', '07/01/2003', '08/01/2003', '09/01/2003', '10/01/2003', '11/01/2003'],
      markers: {
        size: [0, 0, 0],
        strokeWidth: 2,
        hover: {
          size: 4,
        },
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
        axisTicks: {
          show: false,
        },
        axisBorder: {
          show: false,
        },
      },
      grid: {
        show: true,
        xaxis: {
          lines: {
            show: true,
          },
        },
        yaxis: {
          lines: {
            show: false,
          },
        },
        padding: {
          top: 0,
          right: -2,
          bottom: 15,
          left: 10,
        },
      },
      legend: {
        show: true,
        horizontalAlign: "center",
        offsetX: 0,
        offsetY: -5,
        markers: {
          width: 9,
          height: 9,
          radius: 6,
        },
        itemMargin: {
          horizontal: 10,
          vertical: 0,
        },
      },
      plotOptions: {
        bar: {
          columnWidth: "30%",
          barHeight: "70%",
        },
      },
    };
  }

  /**
 *  Sales Category
 */
  private _SalesCategoryChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.SalesCategoryChart = {
      series: [44, 55, 41, 17, 15],
      labels: ["Direct", "Social", "Email", "Other", "Referrals"],
      chart: {
        height: 333,
        type: "donut",
      },
      legend: {
        position: "bottom",
      },
      stroke: {
        show: false
      },
      dataLabels: {
        dropShadow: {
          enabled: false,
        },
      },
      colors: colors
    };
  }

  /**
  * Fetches the data
  */
  private fetchData() {
    this.BestSelling = BestSelling;
    this.TopSelling = TopSelling;
    this.Recentelling = Recentelling;
    this.statData = statData;
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
 * Swiper Vertical  
   */
  Vertical: SwiperOptions = {
    pagination: { el: '.swiper-pagination', clickable: true },
    direction: 'vertical',
    slidesPerView: 2,
    spaceBetween: 0,
    mousewheel: true,
  };

  /**
   * Recent Activity
   */
  toggleActivity() {
    const recentActivity = document.querySelector('.layout-rightside-col');
    if (recentActivity != null) {
      recentActivity.classList.toggle('d-none');
    }

    if (document.documentElement.clientWidth <= 767) {
      const recentActivity = document.querySelector('.layout-rightside-col');
      if (recentActivity != null) {
        recentActivity.classList.add('d-block');
        recentActivity.classList.remove('d-none');
      }
    }
  }

  /**
   * SidebarHide modal
   * @param content modal content
   */
  SidebarHide() {
    const recentActivity = document.querySelector('.layout-rightside-col');
    if (recentActivity != null) {
      recentActivity.classList.remove('d-block');
    }
  }

}
