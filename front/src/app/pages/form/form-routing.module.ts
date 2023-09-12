import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { ValidationComponent } from "./validation/validation.component";
import { WizardComponent } from "./wizard/wizard.component";
import { LayoutsComponent } from "./layouts/layouts.component";

const routes: Routes = [
  {
    path:"validation",
    component: ValidationComponent
  },
  {
    path:"wizard",
    component: WizardComponent
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
