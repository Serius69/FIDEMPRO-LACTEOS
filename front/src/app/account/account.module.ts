import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

import { NgbToastModule } from '@ng-bootstrap/ng-bootstrap';

// Load Icons
import { defineElement  } from 'lord-icon-element';
import lottie from 'lottie-web';

import { ToastsContainer } from './login/toasts-container.component';


import { AccountRoutingModule } from './account-routing.module';
import { SigninModule } from "./auth/signin/signin.module";
import { SignupModule } from "./auth/signup/signup.module";
import { RegisterComponent } from './register/register.component';
import { LoginComponent } from './login/login.component';

@NgModule({
  declarations: [
    RegisterComponent,
    LoginComponent,
    ToastsContainer
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    NgbToastModule,
    AccountRoutingModule,
    SigninModule
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class AccountModule { 
  constructor() {
    defineElement (lottie.loadAnimation);
  }
}
