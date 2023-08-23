// app.routing.ts

import { RouterModule } from "@angular/router";
import { AppComponent } from "./app.component";
import { LoginComponent } from "./components/login/login.component";
import { SignupComponent } from "./components/signup/signup.component";
import { HomeComponent } from "./components/home/home.component";
import { TestComponent } from "./components/test/test.component";

const appRoutes = [
  { path: "", component: AppComponent, pathMatch: "full" },
  { path: "login", component: LoginComponent, pathMatch: "full" },
  { path: "signup", component: SignupComponent, pathMatch: "full" },
  { path: "home", component: HomeComponent, pathMatch: "full" },
  { path: "test", component: TestComponent, pathMatch: "full" },
  { path: "home", component: HomeComponent, pathMatch: "full" },
  { path: "home", component: HomeComponent, pathMatch: "full" },
];
export const routing = RouterModule.forRoot(appRoutes);