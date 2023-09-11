import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Component pages
import { CalendarComponent } from './calendar/calendar.component';
import { ChatComponent } from "./chat/chat.component";
import { MailboxComponent } from "./mailbox/mailbox.component";
import { WidgetsComponent } from "./widgets/widgets.component";
import { EmailBasicComponent } from "./email/email-basic/email-basic.component";
import { EmailEcommerceComponent } from "./email/email-ecommerce/email-ecommerce.component";
import { FileManagerComponent } from "./file-manager/file-manager.component";
import { TodoComponent } from "./todo/todo.component";
import { ApikeyComponent } from './apikey/apikey.component';

const routes: Routes = [
  {
    path: "calendar",
    component: CalendarComponent
  },
  {
    path: "chat",
    component: ChatComponent
  },
  {
    path: "mailbox",
    component: MailboxComponent
  },
  {
    path: "widgets",
    component: WidgetsComponent
  },
  {
    path: "email-basic",
    component: EmailBasicComponent
  },
  {
    path: "email-ecommerce",
    component: EmailEcommerceComponent
  },
  {
    path: "file-manager",
    component: FileManagerComponent
  },
  {
    path: "todo",
    component: TodoComponent
  },
  {
    path: "apikey",
    component: ApikeyComponent
  },
  {
    path: 'jobs', loadChildren: () => import('./jobs/jobs.module').then(m => m.JobsModule)
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AppsRoutingModule { }
