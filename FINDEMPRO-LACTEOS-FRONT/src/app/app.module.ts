import { NgModule ,CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
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
import { FooterComponent } from './components/footer/footer.component';
import { MenuComponent } from './components/menu/menu.component';
import { SettingsThemeComponent } from './components/settings-theme/settings-theme.component';
import { InstructionsComponent } from './components/instructions/instructions.component';
import { CrudComponent } from './components/crud-product/crudproduct.component';
import { ErrorComponent } from './components/error/error.component';
import { ProfileComponent } from './components/profile/profile.component';
import { ResultsComponent } from './components/results/results.component';
import { SimulateComponent } from './components/simulate/simulate.component';
import { PassresetComponent } from './components/auth/passreset/passreset.component';
import { NouserComponent } from './components/auth/nouser/nouser.component';
import { ButtonSettingsComponent } from './components/button-settings/button-settings.component';
import { ChangeComponent } from './components/crud-variable/crudvariable.component';
import { ProfileSettingsComponent } from './components/profile-settings/profile-settings.component';

const routes: Routes = [
  { path: "", component: AppComponent},
  { path: "login", component: LoginComponent},
  { path: "signup", component: SignupComponent },
  { path: "home", component: HomeComponent},
  { path: "instructions", component: InstructionsComponent},
  { path: "product", component: CrudComponent},
  { path: "product/:id", component: CrudComponent},
  { path: "profile", component: ProfileComponent},
  { path: "profile/update", component: ProfileSettingsComponent},
  { path: "results", component: ResultsComponent},
  { path: "simulate", component: SimulateComponent},
  { path: "change", component: ChangeComponent},
  { path: "error", component: ErrorComponent},
  { path: "passreset", component: PassresetComponent},
  { path: "nouser", component: NouserComponent},
];
export const appRoutes: Routes = routes;

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
  imports: [
    RouterModule.forRoot(routes),
    BrowserModule, 
    FormsModule, 
    HttpClientModule],
  providers: [],
  bootstrap: [AppComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class AppModule { }
