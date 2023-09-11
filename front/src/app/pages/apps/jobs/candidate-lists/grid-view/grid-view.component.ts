import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';

import { GridViewModel } from './grid.-viewmodel';
import { GridViewService } from './grid-view.service';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-grid-view',
  templateUrl: './grid-view.component.html',
  styleUrls: ['./grid-view.component.scss'],
  providers: [GridViewService, DecimalPipe]
})
export class GridViewComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  gridview: any;

  // Table data
  candidategrids!: Observable<GridViewModel[]>;
  total: Observable<number>;

  constructor(public service: GridViewService) {
    this.candidategrids = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
* BreadCrumb
*/
    this.breadCrumbItems = [
      { label: 'Candidate Lists' },
      { label: 'Grid View', active: true }
    ];
    // Fetch Data
    setTimeout(() => {
      this.candidategrids.subscribe(x => {
        this.gridview = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200)

  }


}
