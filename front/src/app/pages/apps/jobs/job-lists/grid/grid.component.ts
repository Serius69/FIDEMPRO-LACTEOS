import { DecimalPipe } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';

import { GridModel } from './grid.model';
import { JobGridService } from './grid.service';

@Component({
  selector: 'app-grid',
  templateUrl: './grid.component.html',
  styleUrls: ['./grid.component.scss'],
  providers: [JobGridService, DecimalPipe]
})
export class GridComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  jobgrids: any;

  // Table data
  GridList!: Observable<GridModel[]>;
  total: Observable<number>;

  constructor(public service: JobGridService) {
    this.GridList = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
 * BreadCrumb
 */
    this.breadCrumbItems = [
      { label: 'Jobs' },
      { label: 'Job Grid Lists', active: true }
    ];

    // Fetch Data
    setTimeout(() => {
      this.GridList.subscribe(x => {
        this.jobgrids = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200)

  }


}
