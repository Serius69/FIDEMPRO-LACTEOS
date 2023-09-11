import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Component pages
import { DashboardComponent } from "./dashboards/dashboard/dashboard.component";

const routes: Routes = [
    {
        path: "",
        component: DashboardComponent
    },
    {
      path: '', loadChildren: () => import('./dashboards/dashboards.module').then(m => m.DashboardsModule)
    },
    {
      path: 'home', loadChildren: () => import('./apps/apps.module').then(m => m.AppsModule)
    },
    {
      path: 'product', loadChildren: () => import('./crud/crud.module').then(m => m.CrudModule)
    },
    {
      path: 'simulate', loadChildren: () => import('./simulate/simulate.module').then(m => m.SimulateModule)
    },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PagesRoutingModule { }
