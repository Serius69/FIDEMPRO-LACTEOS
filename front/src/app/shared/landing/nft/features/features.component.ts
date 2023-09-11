import { Component, OnInit } from '@angular/core';

import {featuresModel} from './features.model';
import { featuresData } from './data';

@Component({
  selector: 'app-features',
  templateUrl: './features.component.html',
  styleUrls: ['./features.component.scss']
})

/**
 * Features Component
 */
export class FeaturesComponent implements OnInit {

  featuresData!: featuresModel[];

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
    this.featuresData = featuresData;
  }

}
