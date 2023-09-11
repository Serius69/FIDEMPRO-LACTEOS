import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgbPaginationModule, NgbDropdownModule, NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

// Flat Picker
import { FlatpickrModule } from 'angularx-flatpickr';

// routing
import { JobListsRoutingModule } from './job-lists-routing.module';
import { SharedModule } from 'src/app/shared/shared.module';

// component
import { ListComponent } from './list/list.component';

// Apex Chart Package
import { NgApexchartsModule } from 'ng-apexcharts';
import { GridComponent } from './grid/grid.component';
import { OverviewComponent } from './overview/overview.component';

@NgModule({
  declarations: [
    ListComponent,
    GridComponent,
    OverviewComponent
  ],
  imports: [
    CommonModule,
    JobListsRoutingModule,
    SharedModule,
    NgbPaginationModule,
    NgApexchartsModule,
    FormsModule,
    ReactiveFormsModule,
    FlatpickrModule.forRoot(),
    NgbDropdownModule,
    NgbTooltipModule
  ]
})
export class JobListsModule { }
