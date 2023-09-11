import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { BasicComponent } from "./basic/basic.component";
import { GridjsComponent } from "./gridjs/gridjs.component";
import { ListjsComponent } from "./listjs/listjs.component";

const routes: Routes = [
  {
    path: "basic",
    component: BasicComponent
  },
  {
    path: "gridjs",
    component: GridjsComponent
  },
  {
    path: "listjs",
    component: ListjsComponent
  }
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})

export class TablesRoutingModule { }
