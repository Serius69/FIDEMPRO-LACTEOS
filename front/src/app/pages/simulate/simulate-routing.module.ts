import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { SimulateComponent } from './simulate/simulate.component';
import { InstructionsComponent } from './instructions/instructions.component';
const routes: Routes = [
  {
    path:"simulate/instructions",
    component: InstructionsComponent
  },
  {
    path:"simulation",
    component: SimulateComponent
  },
  
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class SimulateRoutingModule {}
