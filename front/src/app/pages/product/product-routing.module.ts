import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { ListComponent } from './list/list.component';
import { AddComponent } from './add/add.component';
import { OverviewComponent } from './overview/overview.component';
const routes: Routes = [
  {
    path:"list",
    component: ListComponent
  },
  
  {
    path:"overview",
    component: OverviewComponent
  },
  {
    path:"create",
    component: AddComponent
  },
  
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class ProductRoutingModule {}
