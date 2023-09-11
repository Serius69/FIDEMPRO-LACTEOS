import { DecimalPipe } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';

// Data Get
import { candidatelist } from './data';
import { ListViewService } from './list-view.service';
import { ListViewModel } from './list.-viewmodel';

@Component({
  selector: 'app-list-view',
  templateUrl: './list-view.component.html',
  styleUrls: ['./list-view.component.scss'],
  providers: [ListViewService, DecimalPipe]
})
export class ListViewComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  listview: any;

  // Table data
  candidatelists!: Observable<ListViewModel[]>;
  total: Observable<number>;


  constructor(public service: ListViewService) {
    this.candidatelists = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
* BreadCrumb
*/
    this.breadCrumbItems = [
      { label: 'Candidate Lists' },
      { label: 'List View', active: true }
    ];

    // Fetch Data
    setTimeout(() => {
      this.candidatelists.subscribe(x => {
        this.listview = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200)
  }

  bookmarklist(id: any) {
    if (this.listview[id].bookmark == true) {
      this.listview[id].bookmark = false
    } else {
      this.listview[id].bookmark = true
    }
  }

}
