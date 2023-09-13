import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { CrudProductComponent } from './crud/crudproduct.component';
import { AddComponent } from './add/add.component';
const routes: Routes = [
  {
    path:"list",
    component: CrudProductComponent
  },
  {
    path:"add-product",
    component: AddComponent
  },
  
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class ProductRoutingModule {}
