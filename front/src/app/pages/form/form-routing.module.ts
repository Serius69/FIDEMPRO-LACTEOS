import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { BasicComponent } from "./basic/basic.component";
import { SelectComponent } from "./select/select.component";
import { CheckboxsRadiosComponent } from "./checkboxs-radios/checkboxs-radios.component";
import { PickersComponent } from "./pickers/pickers.component";
import { MasksComponent } from "./masks/masks.component";
import { AdvancedComponent } from "./advanced/advanced.component";
import { RangeSlidersComponent } from "./range-sliders/range-sliders.component";
import { ValidationComponent } from "./validation/validation.component";
import { WizardComponent } from "./wizard/wizard.component";
import { EditorsComponent } from "./editors/editors.component";
import { FileUploadsComponent } from "./file-uploads/file-uploads.component";
import { LayoutsComponent } from "./layouts/layouts.component";

const routes: Routes = [
  {
    path:"basic",
    component: BasicComponent
  },
  {
    path:"select",
    component: SelectComponent
  },
  {
    path:"checkboxs-radios",
    component: CheckboxsRadiosComponent
  },
  {
    path:"pickers",
    component: PickersComponent
  },
  {
    path:"masks",
    component: MasksComponent
  },
  {
    path:"advanced",
    component: AdvancedComponent
  },
  {
    path:"range-sliders",
    component: RangeSlidersComponent
  },
  {
    path:"validation",
    component: ValidationComponent
  },
  {
    path:"wizard",
    component: WizardComponent
  },
  {
    path:"editors",
    component: EditorsComponent
  },
  {
    path:"file-uploads",
    component: FileUploadsComponent
  },
  {
    path:"layouts",
    component: LayoutsComponent
  }
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class FormRoutingModule {}
