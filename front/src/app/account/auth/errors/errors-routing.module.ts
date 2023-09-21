import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Components
import { CoverComponent } from "./400/cover.component";
import { Page500Component } from "./500/page500.component";
import { OfflineComponent } from "./300/offline.component";

const routes: Routes = [
  {
    path: "404-cover",
    component: CoverComponent
  },
  {
    path: "page-500",
    component: Page500Component
  },
  {
    path: "offline",
    component: OfflineComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class Error404RoutingModule { }
