import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { LoginComponent } from './components/auth/login/login.component';
import { HeaderComponent } from './components/header/header.component';
import { HomeComponent } from './components/home/home.component';
import { TestComponent } from './components/test/test.component';
import { SignupComponent } from './components/auth/signup/signup.component';
import { Routes, RouterModule, Router} from '@angular/router';
import myAppConfig from './config/my-app-config';

/* login */
import { routing } from "./app.routing";
import { FooterComponent } from './components/footer/footer.component';
import { MenuComponent } from './components/menu/menu.component';
import { SettingsThemeComponent } from './components/settings-theme/settings-theme.component';
import { InstructionsComponent } from './components/instructions/instructions.component';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    HeaderComponent,
    HomeComponent,
    TestComponent,
    SignupComponent,
    FooterComponent,
    MenuComponent,
    SettingsThemeComponent,
    InstructionsComponent
  ],
  imports: [BrowserModule, routing],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
