/**
 * Title Box1 List
 */
export interface TitleBox1Model {
  id: any,
  label: string,
  labelClass: string,
  percentage: string,
  percentageClass: string,
  percentageIcon: string,
  counter: any,
  caption: string,
  icon: string,
  iconClass: string,
  bgColor?: string;
  counterClass?: string,
  captionClass?: string,
  decimals: number,
  prefix: string,
  suffix: string,
}

/**
 * Title Box2 List
 */
export interface TitleBox2Model {
  id: any,
  label: string,
  badge: string,
  icon: string,
  counter: number,
  decimals: number,
  suffix: string,
  prefix: string,
}

/**
 * Title Box3 List
 */
export interface TitleBox3Model {
  id: any,
  bgColor?: string,
  label: string,
  labelClass: string,
  counter?: number,
  counterClass?: string;
  badgeClass: string,
  badge: string,
  percentage: string,
  iconClass: string,
  feaIcon: string,
  subCounter: Array<{
    id?: any;
    counter: number;
    decimals: number;
    suffix: string;
    prefix: string;
  }>;
}

/**
 * Title Box4 List
 */
export interface TitleBox4Model {
  id: any,
  bgColor?: string,
  icon: string,
  iconClass: string,
  label: string,
  labelClass: string,
  counter: number,
  counterClass?: string,
  caption: string,
  captionClass: string,
  percentage: string,
  percentageClass: string,
  badge: string,
  decimals: number,
  separator: string,
  suffix: string,
  prefix: string,
}

/**
 * Title Box4 List
 */
export interface TitleBox5Model {
  id: any,
  bgColor?: string,
  icon: string,
  label: string,
  experience: string,
  companyname: string,
  location: string
}


/**
 * other Widgets List
 */
export interface otherWidgetsModel {
  id: any,
  title: string,
  subTitle: string,
  subItem: Array<{
    id?: any;
    icon: string;
    iconClass: string;
    label: string;
  }>;
  progressBar: Array<{
    id?: any;
    bgColor?: string;
    width: any;
  }>;
}

/**
 * widgets Activities List
 */
export interface widgetsActivitiesModel {
  id: any,
  date: string,
  weekDay: string,
  time: string,
  caption: string,
  subItem: Array<{
    id?: any;
    img?: string;
    imgNumber?: string;
    bgcolor?: string;
    name?: string;
  }>;
}

/**
 * widgets Tasks List
 */
export interface widgetsTasksModel {
  id: any,
  forId: string,
  text: string,
  date: string
}

// Hot Product List
export interface HotproductModel {
  id: any,
  image: string,
  price: string,
  name: string
}

// Candidate
export interface CandidateModel {
  id: any,
  image: string,
  name: string
  insta: string,
  designation: string
}

// Bank card List
export interface BankModel {
  id: any,
  icon: string,
  cardcolor: string,
  card: string,
  amount: string
}

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
