import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Component pages
import { LineComponent } from "./Apexcharts/line/line.component";
import { AreaComponent } from "./Apexcharts/area/area.component";
import { ColumnComponent } from "./Apexcharts/column/column.component";
import { BarComponent } from "./Apexcharts/bar/bar.component";
import { MixedComponent } from "./Apexcharts/mixed/mixed.component";
import { TimelineComponent } from "./Apexcharts/timeline/timeline.component";
import { CandlestickComponent } from "./Apexcharts/candlestick/candlestick.component";
import { BoxplotComponent } from "./Apexcharts/boxplot/boxplot.component";
import { BubbleComponent } from "./Apexcharts/bubble/bubble.component";
import { ScatterComponent } from "./Apexcharts/scatter/scatter.component";
import { HeatmapComponent } from "./Apexcharts/heatmap/heatmap.component";
import { TreemapComponent } from "./Apexcharts/treemap/treemap.component";
import { PieComponent } from "./Apexcharts/pie/pie.component";
import { RadialbarComponent } from "./Apexcharts/radialbar/radialbar.component";
import { RadarComponent } from "./Apexcharts/radar/radar.component";
import { PolarComponent } from "./Apexcharts/polar/polar.component";
import { ChartjsComponent } from "./chartjs/chartjs.component";
import { EchartComponent } from "./echart/echart.component";
import { RangeAreaComponent } from './Apexcharts/range-area/range-area.component';
import { FunnelComponent } from './Apexcharts/funnel/funnel.component';

const routes: Routes = [
  {
    path: "apex-line",
    component: LineComponent
  },
  {
    path: "apex-area",
    component: AreaComponent
  },
  {
    path: "apex-column",
    component: ColumnComponent
  },
  {
    path: "apex-bar",
    component: BarComponent
  },
  {
    path: "apex-mixed",
    component: MixedComponent
  },
  {
    path: "apex-timeline",
    component: TimelineComponent
  },
  {
    path: "apex-candlestick",
    component: CandlestickComponent
  },
  {
    path: "apex-boxplot",
    component: BoxplotComponent
  },
  {
    path: "apex-bubble",
    component: BubbleComponent
  },
  {
    path: "apex-scatter",
    component: ScatterComponent
  },
  {
    path: "apex-heatmap",
    component: HeatmapComponent
  },
  {
    path: "apex-treemap",
    component: TreemapComponent
  },
  {
    path: "apex-pie",
    component: PieComponent
  },
  {
    path: "apex-radialbar",
    component: RadialbarComponent
  },
  {
    path: "apex-radar",
    component: RadarComponent
  },
  {
    path: "apex-polar",
    component: PolarComponent
  },
  {
    path: "chartjs",
    component: ChartjsComponent
  },
  {
    path: "echarts",
    component: EchartComponent
  },
  {
    path: "range-area",
    component: RangeAreaComponent
  },
  {
    path: "funnel",
    component: FunnelComponent
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ChartsRoutingModule { }
