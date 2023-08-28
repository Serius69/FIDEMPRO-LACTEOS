import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { LoginComponent } from './components/auth/login/login.component';
import { HeaderComponent } from './components/header/header.component';
import { HomeComponent } from './components/home/home.component';
import { SignupComponent } from './components/auth/signup/signup.component';
import { Routes, RouterModule, Router} from '@angular/router';
import myAppConfig from './config/my-app-config';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

/* login */
import { routing } from "./app.routing";
import { FooterComponent } from './components/footer/footer.component';
import { MenuComponent } from './components/menu/menu.component';
import { SettingsThemeComponent } from './components/settings-theme/settings-theme.component';
import { InstructionsComponent } from './components/instructions/instructions.component';
import { CrudComponent } from './components/crud/crud.component';
import { ErrorComponent } from './components/error/error.component';
import { ProfileComponent } from './components/profile/profile.component';
import { ResultsComponent } from './components/results/results.component';
import { SimulateComponent } from './components/simulate/simulate.component';
import { PassresetComponent } from './components/auth/passreset/passreset.component';
import { NouserComponent } from './components/auth/nouser/nouser.component';
import { ButtonSettingsComponent } from './components/button-settings/button-settings.component';
import { ChangeComponent } from './components/change/change.component';
import { ProfileSettingsComponent } from './components/profile-settings/profile-settings.component';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    HeaderComponent,
    HomeComponent,
    SignupComponent,
    FooterComponent,
    MenuComponent,
    SettingsThemeComponent,
    InstructionsComponent,
    CrudComponent,
    ErrorComponent,
    ProfileComponent,
    ResultsComponent,
    SimulateComponent,
    PassresetComponent,
    NouserComponent,
    ButtonSettingsComponent,
    ChangeComponent,
    ProfileSettingsComponent
  ],
  imports: [BrowserModule, routing, FormsModule, HttpClientModule],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
