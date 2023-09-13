import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages

import { CreateComponent } from './create/create.component';
import { ListComponent } from '../product/list/list.component';
const routes: Routes = [
  {
    path:"listvariable",
    component: ListComponent
  },
  {
    path:"create",
    component: CreateComponent
  },
  {
    path:"overview",
    component: CreateComponent
  },
  
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class ProductRoutingModule {}
