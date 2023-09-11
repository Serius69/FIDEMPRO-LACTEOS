import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { NgbTooltipModule, NgbDropdownModule, NgbTypeaheadModule, NgbAccordionModule, NgbProgressbarModule, NgbNavModule, NgbPaginationModule, NgbCollapseModule } from '@ng-bootstrap/ng-bootstrap';

// search module
import { Ng2SearchPipeModule } from 'ng2-search-filter';

// Feather Icon
import { FeatherModule } from 'angular-feather';
import { allIcons } from 'angular-feather/icons';

// Calendar package
import { FullCalendarModule } from '@fullcalendar/angular';
// Flat Picker
import { FlatpickrModule } from 'angularx-flatpickr';
// Simplebar
import { SimplebarAngularModule } from 'simplebar-angular';
// Ck Editer
import { CKEditorModule } from '@ckeditor/ckeditor5-angular';
// Counter
import { CountToModule } from 'angular-count-to';
// Apex Chart Package
import { NgApexchartsModule } from 'ng-apexcharts';
import { LeafletModule } from '@asymmetrik/ngx-leaflet';

// Emoji Picker
import { PickerModule } from '@ctrl/ngx-emoji-mart';

//  Drag and drop
import { DndModule } from 'ngx-drag-drop';

// Drag and Droup Row
import { DragDropModule } from '@angular/cdk/drag-drop';
import { MatTableModule } from '@angular/material/table';

// Select Droup down
import { NgSelectModule } from '@ng-select/ng-select';

// Component Pages
import { AppsRoutingModule } from "./apps-routing.module";
import { SharedModule } from '../../shared/shared.module';
import { CalendarComponent } from './calendar/calendar.component';
import { WidgetsComponent } from './widgets/widgets.component';

// Sorting page
import { NgbdApikeySortableHeader } from './apikey/apikey-sortable.directive';

// Load Icon
import { defineElement } from 'lord-icon-element';
import lottie from 'lottie-web';

import { DatePipe } from '@angular/common';
import { TodoComponent } from './todo/todo.component';

import { SortByPipe } from '../apps/sort-by.pipe';
import { ApikeyComponent } from './apikey/apikey.component';

// Mask
import { NgxMaskDirective, NgxMaskPipe, provideNgxMask, IConfig } from 'ngx-mask';

// Swiper Slider
import { NgxUsefulSwiperModule } from 'ngx-useful-swiper';

@NgModule({
  declarations: [
    CalendarComponent,
    WidgetsComponent,
    TodoComponent,
    SortByPipe,
    ApikeyComponent,
    NgbdApikeySortableHeader
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    NgbTooltipModule,
    NgbDropdownModule,
    NgbAccordionModule,
    NgbProgressbarModule,
    NgbNavModule,
    NgbPaginationModule,
    NgbCollapseModule,
    Ng2SearchPipeModule,
    FeatherModule.pick(allIcons),
    FullCalendarModule,
    FlatpickrModule.forRoot(),
    SimplebarAngularModule,
    CKEditorModule,
    CountToModule,
    NgApexchartsModule,
    LeafletModule,
    AppsRoutingModule,
    SharedModule,
    PickerModule,
    DndModule,
    DragDropModule,
    MatTableModule,
    NgSelectModule,
    NgbTypeaheadModule,
    NgxUsefulSwiperModule,
    NgxMaskDirective, NgxMaskPipe
  ],
  providers:[
    provideNgxMask(),
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class AppsModule {
  constructor() {
    defineElement(lottie.loadAnimation);
  }
}
