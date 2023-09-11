import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { DecimalPipe } from '@angular/common';

import { CompaniesListModel } from './companies-lists.model';
import { CompaniesListService } from './companies-list.service';

@Component({
  selector: 'app-companies-list',
  templateUrl: './companies-list.component.html',
  styleUrls: ['./companies-list.component.scss'],
  providers: [CompaniesListService, DecimalPipe]
})
export class CompaniesListComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  companies: any;
  followbtn: any = 1;
  followtxt: any = 'Follow';

  // Table data
  Companieslist!: Observable<CompaniesListModel[]>;
  total: Observable<number>;
  jobdetail: any;

  constructor(public service: CompaniesListService) {
    this.Companieslist = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
* BreadCrumb
*/
    this.breadCrumbItems = [
      { label: 'Companies' },
      { label: 'Companies List', active: true }
    ];

    // Fetch Data
    setTimeout(() => {
      this.Companieslist.subscribe(x => {
        this.companies = Object.assign([], x);
      });
      this.jobdetail = this.companies[0]
      document.getElementById('elmLoader')?.classList.add('d-none')
      document.getElementById('job-overview')?.classList.remove('d-none')
    }, 1200)

  }


  // Go Detail
  companydetail(id: any) {
    this.jobdetail = this.companies[id]
  }

  // Follow - unfollow
  followClick(ev: any) {
    if (this.followbtn == '1') {
      this.followbtn = '2'
      this.followtxt = 'Unfollow'
      document.getElementById('togglefollow')?.classList.replace('btn-soft-success', 'btn-success')
    } else {
      this.followbtn = '1'
      this.followtxt = 'Follow'
      document.getElementById('togglefollow')?.classList.replace('btn-success', 'btn-soft-success')
    }
  }

}
