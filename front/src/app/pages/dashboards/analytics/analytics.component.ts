import { Component, OnInit } from '@angular/core';

import { circle, latLng, tileLayer } from 'leaflet';

import { statData, TopPages } from './data';

@Component({
    selector: 'app-analytics',
    templateUrl: './analytics.component.html',
    styleUrls: ['./analytics.component.scss']
})

/**
 * Analytics Dashboard Component
 */
export class AnalyticsComponent implements OnInit {

    // bread crumb items
    breadCrumbItems!: Array<{}>;
    statData!: any;
    basicBarChart: any;
    basicColumnChart: any;
    basicHeatmapChart: any;
    simpleDonutChart: any;
    TopPages: any;
    isRTL: any = true;

    constructor() {
    }

    ngOnInit(): void {
        /**
         * BreadCrumb
         */
        this.breadCrumbItems = [
            { label: 'Dashboards' },
            { label: 'Analytics', active: true }
        ];

        /**
         * Fetches the data
         */
        this.fetchData();

        // Chart Color Data Get Function
        this._basicBarChart('["--vz-info", "--vz-info", "--vz-info", "--vz-info", "--vz-danger", "--vz-info", "--vz-info", "--vz-info", "--vz-info", "--vz-info"]');
        this._basicColumnChart('["--vz-success", "--vz-light"]');
        this._basicHeatmapChart('["--vz-success", "--vz-info"]');
        this._simpleDonutChart('["--vz-primary", "--vz-warning", "--vz-info"]');
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
    * Basic Bar Chart data
    */
    selectvalue(x: any) {
        if (x == 'all') {
            this.basicBarChart.series = [{
                data: [1010, 1640, 490, 1255, 1050, 689, 800, 420, 1085, 589],
                name: 'Sessions',
            }]
        }
        if (x == '1M') {
            this.basicBarChart.series = [{
                data: [200, 640, 490, 255, 50, 689, 800, 420, 85, 589],
                name: 'Sessions',
            }]
        }
        if (x == '6M') {
            this.basicBarChart.series = [{
                data: [1010, 1640, 490, 1255, 1050, 689, 800, 420, 1085, 589],
                name: 'Sessions',
            }]
        }
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
                height: 400,
                direction: 'rtl',
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
    * Basic Column Chart data
    */
    setcolumnchartvalue(x: any) {
        if (x == 'all') {
            this.basicColumnChart.series = [{
                name: 'Last Year',
                data: [36.2, 22.4, 38.2, 30.5, 26.4, 30.4, 20.2, 29.6, 10.9, 36.2, 22.4, 38.2]
            }, {
                name: 'Current Year',
                data: [36.2, 22.4, 38.2, 30.5, 26.4, 30.4, 20.2, 29.6, 10.9, 36.2, 22.4, 38.2]
            }]
        }
        if (x == '1M') {
            this.basicColumnChart.series = [{
                name: 'Last Year',
                data: [25.3, 12.5, 20.2, 18.5, 40.4, 25.4, 15.8, 22.3, 19.2, 25.3, 12.5, 20.2]
            }, {
                name: 'Current Year',
                data: [25.3, 12.5, 20.2, 18.5, 40.4, 25.4, 15.8, 22.3, 19.2, 25.3, 12.5, 20.2]
            }]
        }
        if (x == '6M') {
            this.basicColumnChart.series = [{
                name: 'Last Year',
                data: [36.2, 22.4, 38.2, 30.5, 26.4, 30.4, 20.2, 29.6, 10.9, 36.2, 22.4, 38.2]
            }, {
                name: 'Current Year',
                data: [25.3, 12.5, 20.2, 18.5, 40.4, 25.4, 15.8, 22.3, 19.2, 25.3, 12.5, 20.2]
            }]
        }
        if (x == '1Y') {
            this.basicColumnChart.series = [{
                name: 'Last Year',
                data: [25.3, 12.5, 20.2, 18.5, 40.4, 25.4, 15.8, 22.3, 19.2, 25.3, 12.5, 20.2]
            }, {
                name: 'Current Year',
                data: [36.2, 22.4, 38.2, 30.5, 26.4, 30.4, 20.2, 29.6, 10.9, 36.2, 22.4, 38.2]
            }]
        }
    }

    /**
   * Basic Column Charts
   */
    private _basicColumnChart(colors: any) {
        colors = this.getChartColorsArray(colors);
        this.basicColumnChart = {
            series: [{
                name: 'Last Year',
                data: [36.2, 22.4, 38.2, 30.5, 26.4, 30.4, 20.2, 29.6, 10.9, 36.2, 22.4, 38.2]
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
                    columnWidth: '20%',
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
            },
            yaxis: {
                show: false
            },
            fill: {
                opacity: 1

            },
            tooltip: {
                y: {
                    formatter: function (val: any) {
                        return "$ " + val + " thousands"
                    }
                }
            }
        };
    }

    /**
  * Basic Heatmap Chart
  */
    private _basicHeatmapChart(colors: any) {
        colors = this.getChartColorsArray(colors);
        this.basicHeatmapChart = {
            series: [{
                name: 'Sat',
                data: this.generateData(18, {
                    min: 0,
                    max: 90
                })
            },
            {
                name: 'Fri',
                data: this.generateData(18, {
                    min: 0,
                    max: 90
                })
            },
            {
                name: 'Thu',
                data: this.generateData(18, {
                    min: 0,
                    max: 90
                })
            },
            {
                name: 'Wed',
                data: this.generateData(18, {
                    min: 0,
                    max: 90
                })
            },
            {
                name: 'Tue',
                data: this.generateData(18, {
                    min: 0,
                    max: 90
                })
            },
            {
                name: 'Mon',
                data: this.generateData(18, {
                    min: 0,
                    max: 90
                })
            },
            {
                name: 'Sun',
                data: this.generateData(18, {
                    min: 0,
                    max: 90
                })
            }
            ],
            chart: {
                height: 400,
                type: 'heatmap',
                offsetX: 0,
                offsetY: -8,
                toolbar: {
                    show: false
                }
            },
            dataLabels: {
                enabled: false
            },
            legend: {
                show: true,
                horizontalAlign: 'center',
                offsetX: 0,
                offsetY: 20,
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
            colors: colors,
            plotOptions: {
                heatmap: {
                    colorScale: {
                        ranges: [{
                            from: 0,
                            to: 50,
                            name: '0-50',
                            color: colors[0]
                        },
                        {
                            from: 51,
                            to: 100,
                            name: '51-00',
                            color: colors[1]
                        },
                        ]
                    }
                }
            },
            tooltip: {
                y: [{
                    formatter: function (y: any) {
                        if (typeof y !== "undefined") {
                            return y.toFixed(0) + "k";
                        }
                        return y;
                    }
                }]
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
    * Fetches the data
    */
    private fetchData() {
        this.statData = statData;
        this.TopPages = TopPages;
    }

}
