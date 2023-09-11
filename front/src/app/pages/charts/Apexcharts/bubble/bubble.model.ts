import {
  ChartComponent,
  ApexAxisChartSeries,
  ApexChart,
  ApexFill,
  ApexXAxis,
  ApexDataLabels,
  ApexYAxis,
  ApexTitleSubtitle,
  ApexTooltip,
  ApexTheme
} from "ng-apexcharts";

export type ChartOptions = {
  series?: ApexAxisChartSeries | any;
  chart?: ApexChart;
  xaxis?: ApexXAxis;
  yaxis?: ApexYAxis;
  title?: ApexTitleSubtitle;
  fill?: ApexFill;
  dataLabels?: ApexDataLabels;
  colors?: string[];
  tooltip?: ApexTooltip;
  theme?: ApexTheme
};
