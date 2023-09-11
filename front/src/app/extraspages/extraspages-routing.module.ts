import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component Pages
import { MaintenanceComponent } from "./maintenance/maintenance.component";
import { ComingSoonComponent } from "./coming-soon/coming-soon.component";

const routes: Routes = [
  {
    path: "maintenance",
    component:MaintenanceComponent
  },
  {
    path: "coming-soon",
    component:ComingSoonComponent
  }
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})

export class ExtrapagesRoutingModule { }
