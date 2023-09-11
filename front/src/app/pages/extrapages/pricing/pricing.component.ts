import { Component, OnInit } from '@angular/core';

import { MonthlyPlanModel, YearlyPlanModel, PricingModel, SimpleModel } from './pricing.model';
import { MonthlyPlan, YearlyPlan, pricingPlan, SimplePlan } from './data';

@Component({
  selector: 'app-pricing',
  templateUrl: './pricing.component.html',
  styleUrls: ['./pricing.component.scss']
})

/**
 * Pricing Component
 */
export class PricingComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  MonthlyPlan!: MonthlyPlanModel[];
  YearlyPlan!: YearlyPlanModel[];
  pricingPlan!: PricingModel[];
  SimplePlan!: SimpleModel[];

  constructor() { }

  ngOnInit(): void {
     /**
    * BreadCrumb
    */
      this.breadCrumbItems = [
        { label: 'Pages' },
        { label: 'Pricing', active: true }
      ];

    // Chat Data Get Function
    this._fetchData();
  }

  // Chat Data Fetch
  private _fetchData() {
    this.MonthlyPlan = MonthlyPlan;
    this.YearlyPlan = YearlyPlan;
    this.pricingPlan = pricingPlan;
    this.SimplePlan = SimplePlan;
  }

}
