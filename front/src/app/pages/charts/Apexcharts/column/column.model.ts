import {
  ApexAxisChartSeries,
  ApexChart,
  ChartComponent,
  ApexDataLabels,
  ApexPlotOptions,
  ApexYAxis,
  ApexLegend,
  ApexStroke,
  ApexXAxis,
  ApexFill,
  ApexTooltip,
  ApexTitleSubtitle,
  ApexResponsive,
  ApexAnnotations,
  ApexGrid,
  ApexStates
} from "ng-apexcharts";

export type ChartOptions = {
  series?: ApexAxisChartSeries | any;
  chart?: ApexChart;
  dataLabels?: ApexDataLabels;
  plotOptions?: ApexPlotOptions;
  yaxis?: ApexYAxis;
  xaxis?: ApexXAxis;
  fill?: ApexFill;
  tooltip?: ApexTooltip;
  stroke?: ApexStroke;
  legend?: ApexLegend;
  title?: ApexTitleSubtitle;
  responsive?: ApexResponsive[];
  colors?: string[];
  annotations?: ApexAnnotations;
  grid?: ApexGrid;
  subtitle?: ApexTitleSubtitle;
  states?: ApexStates;
};
