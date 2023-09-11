import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { DecimalPipe } from '@angular/common';

import { JobCategoriesModel } from './job-categories.model';
import { JobCategoriesService } from './job-categories.service';

@Component({
  selector: 'app-job-categories',
  templateUrl: './job-categories.component.html',
  styleUrls: ['./job-categories.component.scss'],
  providers: [JobCategoriesService, DecimalPipe]
})
export class JobCategoriesComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  categories: any;

  // Table data
  Categorieslist!: Observable<JobCategoriesModel[]>;
  total: Observable<number>;

  constructor(public service: JobCategoriesService) {
    this.Categorieslist = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
* BreadCrumb
*/
    this.breadCrumbItems = [
      { label: 'Jobs' },
      { label: 'Job Categories', active: true }
    ];

    // Fetch Data
    setTimeout(() => {
      this.Categorieslist.subscribe(x => {
        this.categories = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
      document.getElementById('loadmore')?.classList.remove('d-none')
    }, 1200)
  }

}
