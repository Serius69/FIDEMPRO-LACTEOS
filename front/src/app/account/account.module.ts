import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

import { NgbToastModule } from '@ng-bootstrap/ng-bootstrap';

// Load Icons
import { defineElement  } from 'lord-icon-element';
import lottie from 'lottie-web';


import { AccountRoutingModule } from './account-routing.module';
import { LoginComponent } from './auth/login/login.component';
import { RegisterComponent } from './auth/register/register.component';
import { ToastsContainer } from './auth/login/toasts-container.component';
import { LockscreenComponent } from './auth/lockscreen/lockscreen.component';
import { LogoutComponent } from './auth/logout/logout.component';
import { PassCreateComponent } from './auth/pass-create/pass-create.component';
import { PassResetComponent } from './auth/pass-reset/pass-reset.component';
import { SuccessMsgComponent } from './auth/success-msg/success-msg.component';

@NgModule({
  declarations: [
    RegisterComponent,
    LoginComponent,
    ToastsContainer,
    LockscreenComponent,
    LogoutComponent,
    PassCreateComponent,
    PassResetComponent,
    SuccessMsgComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    NgbToastModule,
    AccountRoutingModule,
    
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class AccountModule { 
  constructor() {
    defineElement (lottie.loadAnimation);
  }
}
