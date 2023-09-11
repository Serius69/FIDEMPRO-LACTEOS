import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-terms-condition',
  templateUrl: './terms-condition.component.html',
  styleUrls: ['./terms-condition.component.scss']
})
export class TermsConditionComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  constructor() { }

  ngOnInit(): void {
    /**
   * BreadCrumb
   */
    this.breadCrumbItems = [
      { label: 'Pages' },
      { label: 'Term & Conditions', active: true }
    ];
  }
}
