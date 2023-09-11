import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-email-basic',
  templateUrl: './email-basic.component.html',
  styleUrls: ['./email-basic.component.scss']
})

/**
 * Email-Basic Component
 */
export class EmailBasicComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  constructor() { }

  ngOnInit(): void {
    /**
     * BreadCrumb
     */
     this.breadCrumbItems = [
      { label: 'Email' },
      { label: 'Basic Action', active: true }
    ];
  }

}
