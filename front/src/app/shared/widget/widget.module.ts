import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { NgbTooltipModule, NgbProgressbarModule, NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { CountToModule } from 'angular-count-to';
// Feather Icon
import { FeatherModule } from 'angular-feather';
import { allIcons } from 'angular-feather/icons';
// Apex Chart Package
import { NgApexchartsModule } from 'ng-apexcharts';

import { BestSellingComponent } from './dashboard/best-selling/best-selling.component';
import { TopSellingComponent } from './dashboard/top-selling/top-selling.component';
import { RecentOrdersComponent } from './dashboard/recent-orders/recent-orders.component';
import { StatComponent } from './dashboard/stat/stat.component';
import { TopPagesComponent } from './analytics/top-pages/top-pages.component';
import { AnalaticsStatComponent } from './analytics/analatics-stat/analatics-stat.component';
import { CrmStatComponent } from './crm/crm-stat/crm-stat.component';
import { DealsStatusComponent } from './crm/deals-status/deals-status.component';
import { UpcomingActivitiesComponent } from './crm/upcoming-activities/upcoming-activities.component';
import { ClosingDealsComponent } from './crm/closing-deals/closing-deals.component';
import { CryptoStatComponent } from './crypto/crypto-stat/crypto-stat.component';
import { CurrenciesComponent } from './crypto/currencies/currencies.component';
import { TopPerformersComponent } from './crypto/top-performers/top-performers.component';
import { NewsFeedComponent } from './crypto/news-feed/news-feed.component';
import { ProjectsStatComponent } from './projects/projects-stat/projects-stat.component';
import { ActiveProjectComponent } from './projects/active-project/active-project.component';
import { MyTaskComponent } from './projects/my-task/my-task.component';
import { TeamMembersComponent } from './projects/team-members/team-members.component';
import { NftStatComponent } from './nft/nft-stat/nft-stat.component';

@NgModule({
  declarations: [
    BestSellingComponent,
    TopSellingComponent,
    RecentOrdersComponent,
    TopPagesComponent,
    StatComponent,
    AnalaticsStatComponent,
    CrmStatComponent,
    DealsStatusComponent,
    UpcomingActivitiesComponent,
    ClosingDealsComponent,
    CryptoStatComponent,
    CurrenciesComponent,
    TopPerformersComponent,
    NewsFeedComponent,
    ProjectsStatComponent,
    ActiveProjectComponent,
    MyTaskComponent,
    TeamMembersComponent,
    NftStatComponent,
  ],
  imports: [
    CommonModule,
    NgbTooltipModule,
    NgbProgressbarModule,
    NgbDropdownModule,
    CountToModule,
    FeatherModule.pick(allIcons),
    NgApexchartsModule,
  ],
  exports: [BestSellingComponent, TopSellingComponent, RecentOrdersComponent, TopPagesComponent, StatComponent, AnalaticsStatComponent, CrmStatComponent, DealsStatusComponent, UpcomingActivitiesComponent, ClosingDealsComponent, CryptoStatComponent, CurrenciesComponent, TopPerformersComponent, NewsFeedComponent, ProjectsStatComponent, ActiveProjectComponent, MyTaskComponent, TeamMembersComponent,
    NftStatComponent]
})
export class WidgetModule { }
