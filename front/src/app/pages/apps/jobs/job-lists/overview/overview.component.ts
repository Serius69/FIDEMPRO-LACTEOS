import { Component, OnInit } from '@angular/core';

// Data Get
import { related } from './data';

@Component({
  selector: 'app-overview',
  templateUrl: './overview.component.html',
  styleUrls: ['./overview.component.scss']
})
export class OverviewComponent implements OnInit {

  relatedjobs: any;
  bookmark: boolean = true;

  constructor() { }

  ngOnInit(): void {
    // Fetch Data
    this.relatedjobs = related
  }

  bookmarklist() {
    if (this.bookmark == true) {
      this.bookmark = false
    } else {
      this.bookmark = true
    }
  }

}
