import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbTooltipModule, NgbProgressbarModule, NgbDropdownModule, NgbNavModule, NgbPaginationModule } from '@ng-bootstrap/ng-bootstrap';
// Select Droup down
import { NgSelectModule } from '@ng-select/ng-select';
// Ui Switch
import { UiSwitchModule } from 'ngx-ui-switch';
// FlatPicker
import { FlatpickrModule } from 'angularx-flatpickr';
// Color Picker
import { ColorPickerModule } from 'ngx-color-picker';
// Mask
import { NgxMaskDirective, NgxMaskPipe, provideNgxMask, IConfig } from 'ngx-mask';
// Ngx Sliders
import { NgxSliderModule } from '@angular-slider/ngx-slider';
//Wizard
import { ArchwizardModule } from 'angular-archwizard';
// Ck Editer
import { CKEditorModule } from '@ckeditor/ckeditor5-angular';
// Drop Zone
import { DropzoneModule } from 'ngx-dropzone-wrapper';
import { DROPZONE_CONFIG } from 'ngx-dropzone-wrapper';
import { DropzoneConfigInterface } from 'ngx-dropzone-wrapper';
// Auto Complate
import {AutocompleteLibModule} from 'angular-ng-autocomplete';

// Load Icons
import { defineElement } from 'lord-icon-element';
import lottie from 'lottie-web';

// Feather Icon
import { FeatherModule } from 'angular-feather';
import { allIcons } from 'angular-feather/icons';
// Simple bar
import { SimplebarAngularModule } from 'simplebar-angular';
// Ng Select

// Component pages
import { ListComponent } from './list/list.component';
import { AddComponent } from './add/add.component';
import { ProductRoutingModule } from './product-routing.module';
import { OverviewComponent } from './overview/overview.component';

const DEFAULT_DROPZONE_CONFIG: DropzoneConfigInterface = {
  url: 'https://httpbin.org/post',
  maxFilesize: 50,
  acceptedFiles: 'image/*'
};
@NgModule({
  declarations: [
    ListComponent,
    OverviewComponent,
    AddComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    NgbDropdownModule,
    NgbNavModule,
    NgSelectModule,
    UiSwitchModule,
    FlatpickrModule,
    ColorPickerModule,
    NgxSliderModule,
    ArchwizardModule,
    CKEditorModule,
    DropzoneModule,
    AutocompleteLibModule,
    ProductRoutingModule,
    NgbTooltipModule,
    FeatherModule.pick(allIcons),
    SimplebarAngularModule
  ],
  providers:[
    provideNgxMask(),
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class ProductModule { 
  constructor() {
    defineElement(lottie.loadAnimation);
  }
}
