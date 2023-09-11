import {
    ChartComponent,
    ApexAxisChartSeries,
    ApexPlotOptions,
    ApexChart,
    ApexXAxis,
    ApexDataLabels,
    ApexTitleSubtitle,
    ApexStroke,
    ApexGrid,
    ApexMarkers,
    ApexFill,
    ApexYAxis,
    ApexTooltip,
    ApexLegend,
    ApexAnnotations,
    ApexTheme
  } from "ng-apexcharts";
  
  export type ChartOptions = {
    series?: ApexAxisChartSeries | any;
    chart?: ApexChart;
    xaxis?: ApexXAxis;
    dataLabels?: ApexDataLabels;
    grid?: ApexGrid;
    stroke?: ApexStroke;
    title?: ApexTitleSubtitle;
    markers?: ApexMarkers;
    colors?: string[];
    fill?: ApexFill;
    yaxis?: ApexYAxis | ApexYAxis[];
    tooltip?: ApexTooltip;
    legend?: ApexLegend;
    annotations?: ApexAnnotations;
    labels?: string[] | number[];
    toolbar?: any;
    subtitle?: ApexTitleSubtitle;
    plotOptions?: ApexPlotOptions;
    theme?: ApexTheme
  };
  