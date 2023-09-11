import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { ListComponent } from "./list/list.component";
import { OverviewComponent } from "./overview/overview.component";
import { CreateComponent } from "./create/create.component";

const routes: Routes = [
  {
    path: "list",
    component: ListComponent
  },
  {
    path: "overview",
    component: OverviewComponent
  },
  {
    path: "create",
    component: CreateComponent
  }
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class ProjectsRoutingModule {}
