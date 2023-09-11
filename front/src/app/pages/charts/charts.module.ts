
import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// Apex Chart
import { NgApexchartsModule } from "ng-apexcharts";

import { NgChartsModule } from 'ng2-charts';
import { NgxEchartsModule } from 'ngx-echarts';

// Component Pages
import { ChartsRoutingModule } from "./charts-routing.module";
import { SharedModule } from '../../shared/shared.module';
import { LineComponent } from './Apexcharts/line/line.component';
import { AreaComponent } from './Apexcharts/area/area.component';
import { ColumnComponent } from './Apexcharts/column/column.component';
import { BarComponent } from './Apexcharts/bar/bar.component';
import { MixedComponent } from './Apexcharts/mixed/mixed.component';
import { TimelineComponent } from './Apexcharts/timeline/timeline.component';
import { CandlestickComponent } from './Apexcharts/candlestick/candlestick.component';
import { BoxplotComponent } from './Apexcharts/boxplot/boxplot.component';
import { BubbleComponent } from './Apexcharts/bubble/bubble.component';
import { ScatterComponent } from './Apexcharts/scatter/scatter.component';
import { HeatmapComponent } from './Apexcharts/heatmap/heatmap.component';
import { TreemapComponent } from './Apexcharts/treemap/treemap.component';
import { PieComponent } from './Apexcharts/pie/pie.component';
import { RadialbarComponent } from './Apexcharts/radialbar/radialbar.component';
import { RadarComponent } from './Apexcharts/radar/radar.component';
import { PolarComponent } from './Apexcharts/polar/polar.component';
import { ChartjsComponent } from './chartjs/chartjs.component';
import { EchartComponent } from './echart/echart.component';
import { RangeAreaComponent } from './Apexcharts/range-area/range-area.component';
import { FunnelComponent } from './Apexcharts/funnel/funnel.component';

@NgModule({
  declarations: [
    LineComponent,
    AreaComponent,
    ColumnComponent,
    BarComponent,
    MixedComponent,
    TimelineComponent,
    CandlestickComponent,
    BoxplotComponent,
    BubbleComponent,
    ScatterComponent,
    HeatmapComponent,
    TreemapComponent,
    PieComponent,
    RadialbarComponent,
    RadarComponent,
    PolarComponent,
    ChartjsComponent,
    EchartComponent,
    RangeAreaComponent,
    FunnelComponent
  ],
  imports: [
    CommonModule,
    NgApexchartsModule,
    NgChartsModule,
    ChartsRoutingModule,
    SharedModule,
    NgxEchartsModule.forRoot({
      echarts: () => import('echarts')
    })
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class ChartsModule { }
