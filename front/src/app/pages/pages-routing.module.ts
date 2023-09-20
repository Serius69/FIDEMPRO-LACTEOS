import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Component pages
import { DashboardComponent } from "./dashboards/dashboard/dashboard.component";

const routes: Routes = [
    {
      path: '', loadChildren: () => import('./home/home.module').then(m => m.HomeModule)
    },
    {
      path: 'dashboard', loadChildren: () => import('./dashboards/dashboards.module').then(m => m.DashboardsModule)
    },
    {
      path: 'product', loadChildren: () => import('./product/product.module').then(m => m.ProductModule)
    },    
    {
      path: 'variable', loadChildren: () => import('./variable/variable.module').then(m => m.VariableModule)
    },
    {
      path: 'simulate', loadChildren: () => import('./simulate/simulate.module').then(m => m.SimulateModule)
    },
    {
      path: 'pages', loadChildren: () => import('./extrapages/extraspages.module').then(m => m.ExtraspagesModule)
    },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PagesRoutingModule { }
