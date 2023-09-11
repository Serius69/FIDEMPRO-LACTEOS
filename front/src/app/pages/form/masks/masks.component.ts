import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-masks',
  templateUrl: './masks.component.html',
  styleUrls: ['./masks.component.scss']
})

/**
 * Masks Component
 */
export class MasksComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Forms' },
      { label: 'Input Masks', active: true }
    ];
  }

}
