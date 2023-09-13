import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbDropdownModule, NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
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

// Component pages
import { CrudVariableComponent } from './crud/crudvariable.component';
import { CreateComponent } from './create/create.component';

const DEFAULT_DROPZONE_CONFIG: DropzoneConfigInterface = {
  url: 'https://httpbin.org/post',
  maxFilesize: 50,
  acceptedFiles: 'image/*'
};
@NgModule({
  declarations: [
    CrudVariableComponent,
    CreateComponent
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
    AutocompleteLibModule
  ],
  providers:[
    provideNgxMask(),
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class VariableModule {
  constructor() {
    defineElement(lottie.loadAnimation);
  }
 }
