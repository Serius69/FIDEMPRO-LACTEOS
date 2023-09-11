import { Component, OnInit, Input } from '@angular/core';

import {status1, status2, status3, status4, status5, status6, status7 } from './data';
import { ChartType } from './team-members.model';

@Component({
  selector: 'app-team-members',
  templateUrl: './team-members.component.html',
  styleUrls: ['./team-members.component.scss']
})

/**
 * Team Members Component
 */
export class TeamMembersComponent implements OnInit {

  // Team Members
  @Input() TeamMembers: Array<{
    name?: string;
    dedline?: string;
    status?: string;
    assignee: {
      name?: string;
      profile?: string;
    };
  }> | undefined;

  status1!: ChartType;
  status2!: ChartType;
  status3!: ChartType;
  status4!: ChartType;
  status5!: ChartType;
  status6!: ChartType;
  status7!: ChartType;

  constructor() { }

  ngOnInit(): void {
    /**
     * Fetches the data
     */
     this.fetchData();
   
  }

   /**
   * Fetches the data
   */
    private fetchData() {
      this.status1 = status1;
      this.status2 = status2;
      this.status3 = status3;
      this.status4 = status4;
      this.status5 = status5;
      this.status6 = status6;
      this.status7 = status7;
    }

}
