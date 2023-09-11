import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Component pages
import { CalendarComponent } from './calendar/calendar.component';
import { WidgetsComponent } from "./widgets/widgets.component";
import { TodoComponent } from "./todo/todo.component";
import { ApikeyComponent } from './apikey/apikey.component';

const routes: Routes = [
  {
    path: "calendar",
    component: CalendarComponent
  },
  {
    path: "widgets",
    component: WidgetsComponent
  },
  {
    path: "todo",
    component: TodoComponent
  },
  {
    path: "apikey",
    component: ApikeyComponent
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AppsRoutingModule { }
