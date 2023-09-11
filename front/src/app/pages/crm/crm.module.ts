import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgbPaginationModule, NgbTypeaheadModule, NgbTooltipModule, NgbDropdownModule, NgbAccordionModule } from '@ng-bootstrap/ng-bootstrap';

// Flat Picker
import { FlatpickrModule } from 'angularx-flatpickr';

// Ng Select
import { NgSelectModule } from '@ng-select/ng-select';

// Load Icons
import { defineElement } from 'lord-icon-element';
import lottie from 'lottie-web';

// Component pages
import { CRMRoutingModule } from './crm-routing.module';
import { SharedModule } from '../../shared/shared.module';
import { ContactsComponent } from './contacts/contacts.component';
import { CompaniesComponent } from './companies/companies.component';
import { DealsComponent } from './deals/deals.component';
import { LeadsComponent } from './leads/leads.component';

import { SortByCrmPipe } from "../crm/sort-by.pipe";
// sortable
import { NgbdCompaniesSortableHeader } from './companies/companies-sortable.directive';
import { NgbdContactsSortableHeader } from './contacts/contacts-sortable.directive';
import {NgbdLeadsSortableHeader} from './leads/leads-sortable.directive';

import { DatePipe } from '@angular/common';

@NgModule({
  declarations: [
    ContactsComponent,
    CompaniesComponent,
    DealsComponent,
    LeadsComponent,
    SortByCrmPipe,
    NgbdCompaniesSortableHeader,
    NgbdContactsSortableHeader,
    NgbdLeadsSortableHeader


  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    NgbPaginationModule,
    NgbTypeaheadModule,
    NgbTooltipModule,
    NgbDropdownModule,
    NgbAccordionModule,
    FlatpickrModule,
    NgSelectModule,
    CRMRoutingModule,
    SharedModule
  ],
  providers: [
    DatePipe
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class CrmModule {
  constructor() {
    defineElement(lottie.loadAnimation);
  }
}
