import { Component, OnInit } from '@angular/core';

import {servicesModel} from './services.module';
import { Services } from './data';

@Component({
  selector: 'app-services',
  templateUrl: './services.component.html',
  styleUrls: ['./services.component.scss']
})

/**
 * Services Component
 */
export class ServicesComponent implements OnInit {

  Services!: servicesModel[];

  constructor() { }

  ngOnInit(): void {
    /**
     * fetches data
     */
     this._fetchData();
  }

  /**
 * User grid data fetches
 */
    private _fetchData() {
      this.Services = Services;
    }

}
