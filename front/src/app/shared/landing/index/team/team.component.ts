import { Component, OnInit } from '@angular/core';

import {TeamModel} from './team.module';
import { Teams } from './data';

@Component({
  selector: 'app-team',
  templateUrl: './team.component.html',
  styleUrls: ['./team.component.scss']
})

/**
 * Team Component
 */
export class TeamComponent implements OnInit {

  Teams!: TeamModel[];

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
    this.Teams = Teams;
  }

}
