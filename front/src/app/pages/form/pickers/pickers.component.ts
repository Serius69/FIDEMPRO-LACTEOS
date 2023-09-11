import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-pickers',
  templateUrl: './pickers.component.html',
  styleUrls: ['./pickers.component.scss']
})

/**
 * Pickers Component
 */
export class PickersComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  componentcolor!: string;
  monolith!: string;
  nano!: string;

  modelValueAsDate: Date = new Date();

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Forms' },
      { label: 'Pickers', active: true }
    ];
  }

  inlineDatePicker: Date = new Date();

}
