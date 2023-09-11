import { Component, OnInit } from '@angular/core';

import {ProcessModel} from './work-process.module';
import { Process } from './data';

@Component({
  selector: 'app-work-process',
  templateUrl: './work-process.component.html',
  styleUrls: ['./work-process.component.scss']
})

/**
 * WorkProcess Component
 */
export class WorkProcessComponent implements OnInit {

  Process!: ProcessModel[];
  
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
    this.Process = Process;
  }

}
