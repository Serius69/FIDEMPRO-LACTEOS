import {
  ChartComponent,
  ApexAxisChartSeries,
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
  ApexAnnotations
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
  yaxis?: ApexYAxis;
  tooltip?: ApexTooltip;
  legend?: ApexLegend;
  annotations?: ApexAnnotations;
  labels?: string[] | number[];
  toolbar?: any;
};
