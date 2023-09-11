import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Component pages
import { ListComponent } from './list/list.component';
import { GridComponent } from './grid/grid.component';
import { OverviewComponent } from './overview/overview.component';

const routes: Routes = [
  {
    path: "list",
    component: ListComponent
  },
  {
    path: "grid",
    component: GridComponent
  },
  {
    path: "overview",
    component: OverviewComponent
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class JobListsRoutingModule { }
