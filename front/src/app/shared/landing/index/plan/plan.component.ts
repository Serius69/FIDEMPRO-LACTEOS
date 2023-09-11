import { Component, OnInit } from '@angular/core';

import { MonthlyPlanModel, AnnualPlanModel } from './plan.module';
import { MonthlyPlan, AnnualPlan } from './data';

@Component({
  selector: 'app-plan',
  templateUrl: './plan.component.html',
  styleUrls: ['./plan.component.scss']
})

/**
 * Plan Component
 */
export class PlanComponent implements OnInit {


  MonthlyPlan!: MonthlyPlanModel[];
  AnnualPlan!: AnnualPlanModel[];

  constructor() { }

  ngOnInit(): void {
    // Chat Data Get Function
    this._fetchData();
    document.querySelectorAll(".annual").forEach((item)=>{
      item.setAttribute('style','display:none')
    })
  }

   // Chat Data Fetch
   private _fetchData() {
    this.MonthlyPlan = MonthlyPlan;
    this.AnnualPlan = AnnualPlan;
  }

  /**
   * Open modal
   * @param content modal content
   */
   
   check() {
    var checkBox = document.getElementById("plan-switch");
    var month = document.querySelectorAll(".month");
    var annual = document.querySelectorAll(".annual");

    
    annual.forEach((item)=>{
      if(item.getAttribute('style')=='display:none')
      {
        item.setAttribute('style','display:block')
      }else{
        item.setAttribute('style','display:none')
      }
    })
    month.forEach((item)=>{
      if(item.getAttribute('style')=='display:none')
      {
        item.setAttribute('style','display:block')
      }else{
        item.setAttribute('style','display:none')
      }
    });
    
  }

}
