import { Component, OnInit } from '@angular/core';

import {discoverModel} from './discover.model';
import { discoverData } from './data';

@Component({
  selector: 'app-discover',
  templateUrl: './discover.component.html',
  styleUrls: ['./discover.component.scss']
})

/**
 * Discover Component
 */
export class DiscoverComponent implements OnInit {

  discoverData!: discoverModel[];

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
    this.discoverData = discoverData;
  }

  /**
   * Active Toggle navbar
   */
   activeMenu(id:any) {            
    document.querySelector('.heart_icon_'+id)?.classList.toggle('active');
  }

}
