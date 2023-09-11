import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbNavModule, NgbDropdownModule, NgbAccordionModule, NgbTooltipModule, NgbPaginationModule } from '@ng-bootstrap/ng-bootstrap';

// Swiper Slider
import { NgxUsefulSwiperModule } from 'ngx-useful-swiper';
// Select Droup down
import { NgSelectModule } from '@ng-select/ng-select';
// Flatpicker
import { FlatpickrModule } from 'angularx-flatpickr';

// Feather Icon
import { FeatherModule } from 'angular-feather';
import { allIcons } from 'angular-feather/icons';

// Ng Search 
import { Ng2SearchPipeModule } from 'ng2-search-filter';

// Load Icon
import { defineElement } from 'lord-icon-element';
import lottie from 'lottie-web';

// Component pages
import { ExtraPagesRoutingModule } from './extrapages-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { StarterComponent } from './starter/starter.component';
import { ProfileComponent } from './profile/profile/profile.component';
import { SettingsComponent } from './profile/settings/settings.component';
import { TeamComponent } from './team/team.component';
import { TimelineComponent } from './timeline/timeline.component';
import { FaqsComponent } from './faqs/faqs.component';
import { PricingComponent } from './pricing/pricing.component';
import { GalleryComponent } from './gallery/gallery.component';
import { SitemapComponent } from './sitemap/sitemap.component';
import { SearchResultsComponent } from './search-results/search-results.component';
import { PrivacyPolicyComponent } from './privacy-policy/privacy-policy.component';
import { TermsConditionComponent } from './terms-condition/terms-condition.component';

@NgModule({
  declarations: [
    StarterComponent,
    ProfileComponent,
    SettingsComponent,
    TeamComponent,
    TimelineComponent,
    FaqsComponent,
    PricingComponent,
    GalleryComponent,
    SitemapComponent,
    SearchResultsComponent,
    PrivacyPolicyComponent,
    TermsConditionComponent
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    NgbNavModule,
    NgbDropdownModule,
    NgbAccordionModule,
    NgbTooltipModule,
    NgbPaginationModule,
    NgxUsefulSwiperModule,
    NgSelectModule,
    FlatpickrModule,
    ExtraPagesRoutingModule,
    SharedModule,
    FeatherModule.pick(allIcons),
    Ng2SearchPipeModule
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class ExtraspagesModule { 
  constructor() {
    defineElement(lottie.loadAnimation);
  }
}
