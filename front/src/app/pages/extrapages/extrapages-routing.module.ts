import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// Component pages
import { ProfileComponent } from "./profile/profile/profile.component";
import { SettingsComponent } from "./profile/settings/settings.component";
import { FaqsComponent } from "./faqs/faqs.component";
import { SitemapComponent } from "./sitemap/sitemap.component";
import { PrivacyPolicyComponent } from './privacy-policy/privacy-policy.component';
import { TermsConditionComponent } from './terms-condition/terms-condition.component';

const routes: Routes = [
  {
    path: 'profile',
    component: ProfileComponent
  },
  {
    path: 'profile-setting',
    component: SettingsComponent
  },
  {
    path: 'faqs',
    component: FaqsComponent
  },
  {
    path: 'sitemap',
    component: SitemapComponent
  },
  {
    path: 'privacy-policy',
    component: PrivacyPolicyComponent
  },
  {
    path: 'terms-condition',
    component: TermsConditionComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ExtraPagesRoutingModule { }
