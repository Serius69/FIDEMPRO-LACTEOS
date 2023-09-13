import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { CrudVariableComponent } from './crud/crudvariable.component';
import { CreateComponent } from './create/create.component';
const routes: Routes = [
  {
    path:"list",
    component: CrudVariableComponent
  },
  {
    path:"add-variable",
    component: CreateComponent
  },
  
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class ProductRoutingModule {}
