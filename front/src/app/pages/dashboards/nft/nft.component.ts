import { Component, OnInit } from '@angular/core';
import { interval } from 'rxjs';
import { map } from 'rxjs/operators';
import { circle, latLng, tileLayer } from 'leaflet';

import { SwiperOptions } from 'swiper';

import { statData, featuredData, recentData, topCollectionData, popularData } from './data';
import { featuredModel, recentModel, topCollectionModel, popularModel } from './nft.model';

@Component({
    selector: 'app-nft',
    templateUrl: './nft.component.html',
    styleUrls: ['./nft.component.scss']
})

/**
 * Nft Component
 */
export class NftComponent implements OnInit {

    // bread crumb items
    breadCrumbItems!: Array<{}>;
    statData!: any;
    featuredData!: featuredModel[];
    recentData!: recentModel[];
    topCollectionData!: topCollectionModel[];
    popularData!: popularModel[];

    MarketplaceChart: any;
    popularityChart: any;
    minichart1: any;
    minichart2: any;
    minichart3: any;
    minichart4: any;
    minichart5: any;
    minichart6: any;
    minichart7: any;
    minichart8: any;

    // set the current year
    year: number = new Date().getFullYear();
    private _trialEndsAt: any;
    private _diff?: any;
    _days?: number;
    _hours?: number;
    _minutes?: number;
    _seconds?: number;

    constructor() {
    }

    ngOnInit(): void {
        /**
         * BreadCrumb
         */
        this.breadCrumbItems = [
            { label: 'Dashboards' },
            { label: 'NFT Dashboard', active: true }
        ];

        /**
        * Fetches the data
        */
        this.fetchData();

        this._marketplaceChart('["--vz-primary","--vz-success", "--vz-light"]');
        this._popularityChart('["--vz-success", "--vz-warning"]');
        this._minichart1Chart('["--vz-danger"]');
        this._minichartsuccessChart('["--vz-success"]');

        // Date Set
        this._trialEndsAt = "2023-12-31";

        /**
         * Count date set
         */
        interval(1000).pipe(map((x) => {
            this._diff = Date.parse(this._trialEndsAt) - Date.parse(new Date().toString());
        })).subscribe((x) => {
            this._days = this.getDays(this._diff);
            this._hours = this.getHours(this._diff);
            this._minutes = this.getMinutes(this._diff);
            this._seconds = this.getSeconds(this._diff);
        });

    }

    /**
     * Day Set
     */
    getDays(t: number) {
        return Math.floor(t / (1000 * 60 * 60 * 24));
    }

    /**
     * Hours Set
     */
    getHours(t: number) {
        return Math.floor((t / (1000 * 60 * 60)) % 24);
    }

    /**
     * Minutes set
     */
    getMinutes(t: number) {
        return Math.floor((t / 1000 / 60) % 60);
    }

    /**
     * Secound set
     */
    getSeconds(t: number) {
        return Math.floor((t / 1000) % 60);
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
     * Fetches the data
     */
    private fetchData() {
        this.statData = statData;
        this.featuredData = featuredData;
        this.recentData = recentData;
        this.topCollectionData = topCollectionData;
        this.popularData = popularData;
    }

    /**
     * Swiper Responsive setting
     */
    public Responsive: SwiperOptions = {
        slidesPerView: 1,
        loop: true,
        navigation: true,
        spaceBetween: 25,
        breakpoints: {
            768: {
                slidesPerView: 2,
            },
            1200: {
                slidesPerView: 3,
            }
        }
    };

    /**
     * Top CollectionSwiper Responsive setting
     */
    public collection: SwiperOptions = {
        slidesPerView: 1,
        loop: true,
        spaceBetween: 10
    };

    /**
    * Market Place Chart
    */
    setmarketplacevalue(value: any) {
        if (value == 'all') {
            this.MarketplaceChart.series = [{
                name: "Artwork",
                data: [10, 41, 35, 51, 49, 62, 69, 91, 148]
            },
            {
                name: "Auction",
                data: [40, 120, 83, 45, 31, 74, 35, 34, 78]
            },
            {
                name: "Creators",
                data: [95, 35, 20, 130, 64, 22, 43, 45, 31]
            }]
        }
        if (value == '1M') {
            this.MarketplaceChart.series = [{
                name: "Artwork",
                data: [20,31, 25, 41, 59, 72, 69, 91, 148]
            },
            {
                name: "Auction",
                data: [50, 60, 103, 35, 41, 104, 35, 34, 58]
            },
            {
                name: "Creators",
                data: [95, 35, 20, 130, 64, 22, 43, 45, 31]
            }]
        }
        if (value == '6M') {
            this.MarketplaceChart.series = [{
                name: "Artwork",
                data: [50, 21, 15, 61, 59, 62, 69, 91, 148]
            },
            {
                name: "Auction",
                data: [50, 12, 83, 45, 91, 54, 35, 34, 88]
            },
            {
                name: "Creators",
                data: [85, 45, 70, 130, 94, 12, 23, 45, 31]
            }]
        }
        if (value == '1Y') {
            this.MarketplaceChart.series = [{
                name: "Artwork",
                data: [70, 21, 35, 21, 49, 62, 69, 31, 148]
            },
            {
                name: "Auction",
                data: [90, 120, 23, 45, 71, 74, 35, 24, 88]
            },
            {
                name: "Creators",
                data: [95, 35, 20, 130, 64, 22, 43, 45, 31]
            }]
        }
    }

    private _marketplaceChart(colors: any) {
        colors = this.getChartColorsArray(colors);
        this.MarketplaceChart = {
            series: [{
                name: "Artwork",
                data: [10, 41, 35, 51, 49, 62, 69, 91, 148]
            },
            {
                name: "Auction",
                data: [40, 120, 83, 45, 31, 74, 35, 34, 78]
            },
            {
                name: "Creators",
                data: [95, 35, 20, 130, 64, 22, 43, 45, 31]
            }],
            chart: {
                height: 350,
                type: 'line',
                zoom: {
                    enabled: false
                },
                toolbar: {
                    show: false
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                curve: 'smooth',
                width: 3
            },
            colors: colors,
            xaxis: {
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],
            }
        };
    }

    /**
    * Market Place Chart
    */
    private _popularityChart(colors: any) {
        colors = this.getChartColorsArray(colors);
        this.popularityChart = {
            series: [{
                name: 'Like',
                data: [12.45, 16.2, 8.9, 11.42, 12.6, 18.1, 18.2, 14.16]
            }, {
                name: 'Share',
                data: [-11.45, -15.42, -7.9, -12.42, -12.6, -18.1, -18.2, -14.16]
            }],
            chart: {
                type: 'bar',
                height: 260,
                stacked: true,
                toolbar: {
                    show: false
                },
            },
            plotOptions: {
                bar: {
                    columnWidth: '20%',
                    borderRadius: [4, 4]
                },
            },
            colors: colors,
            fill: {
                opacity: 1
            },
            dataLabels: {
                enabled: false,
                textAnchor: 'top',
            },
            yaxis: {
                labels: {
                    show: false,
                    formatter: function (y: any) {
                        return y.toFixed(0) + "%";
                    }
                }
            },
            legend: {
                position: 'top',
                horizontalAlign: 'right',
            },
            xaxis: {
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                labels: {
                    rotate: -90
                }
            }
        };
    }

    /**
    * Danger Mini Chart
    */
    private _minichart1Chart(colors: any) {
        colors = this.getChartColorsArray(colors);
        this.minichart1 = {
            series: [{
                data: [25, 66, 41, 89, 63, 25, 44, 12]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };

        // mini chart 2
        this.minichart2 = {
            series: [{
                data: [50, 15, 35, 62, 23, 56, 44, 12]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };

        // mini chart 3
        this.minichart3 = {
            series: [{
                data: [25, 35, 35, 89, 63, 25, 44, 12]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };

        // mini chart 6
        this.minichart6 = {
            series: [{
                data: [50, 15, 35, 62, 23, 56, 44, 12]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };

        // mini chart 8
        this.minichart8 = {
            series: [{
                data: [45, 53, 24, 89, 63, 60, 36, 50]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };
    }

    /**
    * Success Mini Chart
    */
    private _minichartsuccessChart(colors: any) {
        colors = this.getChartColorsArray(colors);
        this.minichart4 = {
            series: [{
                data: [50, 15, 20, 34, 23, 56, 65, 41]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };

        // mini chart 5 
        this.minichart5 = {
            series: [{
                data: [45, 53, 24, 89, 63, 60, 36, 50]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
        };

        // mini chart 7
        this.minichart7 = {
            series: [{
                data: [50, 15, 20, 34, 23, 56, 65, 41]
            }],
            chart: {
                type: 'line',
                width: 80,
                height: 30,
                sparkline: {
                    enabled: true
                }

            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2.3,
            },
            tooltip: {
                fixed: {
                    enabled: false
                },
                x: {
                    show: false
                },
                y: {
                    title: {
                        formatter: function (seriesName: any) {
                            return ''
                        }
                    }
                },
                marker: {
                    show: false
                }
            }
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

}
