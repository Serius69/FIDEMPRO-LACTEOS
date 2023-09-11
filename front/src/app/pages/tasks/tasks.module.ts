import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { NgbDropdownModule, NgbNavModule, NgbTooltipModule, NgbProgressbarModule, NgbTypeaheadModule, NgbPaginationModule } from '@ng-bootstrap/ng-bootstrap';

// Simple bar
import { SimplebarAngularModule } from 'simplebar-angular';
//  Drag and drop
import { DndModule } from 'ngx-drag-drop';
// Flat Picker
import { FlatpickrModule } from 'angularx-flatpickr';
// Counter
import { CountToModule } from 'angular-count-to';

// Sorting page
import { NgbdListViewSortableHeader } from './../tasks/list-view/list-view-sortable.directive';

// Load Icons
import { defineElement } from 'lord-icon-element';
import lottie from 'lottie-web';

// Component Pages
import { TasksRoutingModule } from './tasks-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { KanbanComponent } from './kanban/kanban.component';
import { ListViewComponent } from './list-view/list-view.component';
import { DetailsComponent } from './details/details.component';

@NgModule({
  declarations: [
    KanbanComponent,
    ListViewComponent,
    NgbdListViewSortableHeader,
    DetailsComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    NgbDropdownModule,
    NgbNavModule,
    NgbTooltipModule,
    NgbProgressbarModule,
    NgbTypeaheadModule,
    NgbPaginationModule,
    SimplebarAngularModule,
    DndModule,
    FlatpickrModule,
    CountToModule,
    TasksRoutingModule,
    SharedModule
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class TasksModule { 
  constructor() {
    defineElement(lottie.loadAnimation);
  }
}
