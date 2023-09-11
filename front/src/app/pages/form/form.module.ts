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
import { FormRoutingModule } from './form-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { BasicComponent } from './basic/basic.component';
import { SelectComponent } from './select/select.component';
import { CheckboxsRadiosComponent } from './checkboxs-radios/checkboxs-radios.component';
import { PickersComponent } from './pickers/pickers.component';
import { MasksComponent } from './masks/masks.component';
import { AdvancedComponent } from './advanced/advanced.component';
import { RangeSlidersComponent } from './range-sliders/range-sliders.component';
import { ValidationComponent } from './validation/validation.component';
import { WizardComponent } from './wizard/wizard.component';
import { EditorsComponent } from './editors/editors.component';
import { FileUploadsComponent } from './file-uploads/file-uploads.component';
import { LayoutsComponent } from './layouts/layouts.component';

const DEFAULT_DROPZONE_CONFIG: DropzoneConfigInterface = {
  url: 'https://httpbin.org/post',
  maxFilesize: 50,
  acceptedFiles: 'image/*'
};

@NgModule({
  declarations: [
    BasicComponent,
    SelectComponent,
    CheckboxsRadiosComponent,
    PickersComponent,
    MasksComponent,
    AdvancedComponent,
    RangeSlidersComponent,
    ValidationComponent,
    WizardComponent,
    EditorsComponent,
    FileUploadsComponent,
    LayoutsComponent
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
    NgxMaskDirective, 
    NgxMaskPipe,
    NgxSliderModule,
    ArchwizardModule,
    CKEditorModule,
    AutocompleteLibModule,
    FormRoutingModule,
    SharedModule,
    DropzoneModule,
  ],
  providers:[
    provideNgxMask(),
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class FormModule { 
  constructor() {
    defineElement(lottie.loadAnimation);
  }
}
