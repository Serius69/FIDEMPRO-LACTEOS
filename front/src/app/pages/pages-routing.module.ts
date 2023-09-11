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
      path: 'instructions', loadChildren: () => import('./ecommerce/ecommerce.module').then(m => m.EcommerceModule)
    },
    {
      path: 'product', loadChildren: () => import('./projects/projects.module').then(m => m.ProjectsModule)
    },
    {
      path: 'simulate', loadChildren: () => import('./tasks/simulate.module').then(m => m.TasksModule)
    },
    {
      path: 'simulate', loadChildren: () => import('./tasks/simulate.module').then(m => m.TasksModule)
    },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PagesRoutingModule { }
