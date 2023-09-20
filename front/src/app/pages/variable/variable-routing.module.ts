import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages

import { CreateComponent } from './create/create.component';
import { ListComponent } from './list/list.component';
import { OverviewComponent } from './overview/overview.component';
const routes: Routes = [
  {
    path:"variable/list",
    component: ListComponent
  },
  {
    path:"variable/create",
    component: CreateComponent
  },
  {
    path:"variable/overview",
    component: OverviewComponent
  },
  
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class VariableRoutingModule {}
