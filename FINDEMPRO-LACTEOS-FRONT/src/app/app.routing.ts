// app.routing.ts

import { RouterModule } from "@angular/router";
import { AppComponent } from "./app.component";
import { LoginComponent } from "./components/auth/login/login.component";
import { SignupComponent } from "./components/auth/signup/signup.component";
import { HomeComponent } from "./components/home/home.component";
import { InstructionsComponent } from "./components/instructions/instructions.component";
import { CrudComponent } from "./components/crud/crud.component";
import { ProfileComponent } from "./components/profile/profile.component";
import { ResultsComponent } from "./components/results/results.component";
import { SimulateComponent } from "./components/simulate/simulate.component";
import { ErrorComponent } from "./components/error/error.component";
import { PassresetComponent } from "./components/auth/passreset/passreset.component";
import { NouserComponent } from "./components/auth/nouser/nouser.component";
import { ChangeComponent } from "./components/change/change.component";
import { ProfileSettingsComponent } from "./components/profile-settings/profile-settings.component";

const appRoutes = [
  { path: "", component: AppComponent, pathMatch: "full" },
  { path: "login", component: LoginComponent, pathMatch: "full" },
  { path: "signup", component: SignupComponent, pathMatch: "full" },
  { path: "home", component: HomeComponent, pathMatch: "full" },
  { path: "instructions", component: InstructionsComponent, pathMatch: "full" },
  { path: "product", component: CrudComponent, pathMatch: "full" },
  { path: "profile", component: ProfileComponent, pathMatch: "full" },
  { path: "profile/update", component: ProfileSettingsComponent, pathMatch: "full" },
  { path: "results", component: ResultsComponent, pathMatch: "full" },
  { path: "simulate", component: SimulateComponent, pathMatch: "full" },
  { path: "change", component: ChangeComponent, pathMatch: "full" },
  { path: "error", component: ErrorComponent, pathMatch: "full" },
  { path: "passreset", component: PassresetComponent, pathMatch: "full" },
  { path: "nouser", component: NouserComponent, pathMatch: "full" },
];
export const routing = RouterModule.forRoot(appRoutes);