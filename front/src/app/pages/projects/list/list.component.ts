import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

import { projectListWidgets, projectListWidgets1, projectListWidgets2 } from './data';
import { projectListModel, projectListModel1, projectListModel2 } from './list.model';
import { listService } from './list.service';
import { DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-list',
  templateUrl: './list.component.html',
  styleUrls: ['./list.component.scss'],
  providers: [listService, DecimalPipe]
})

/**
 * List Component
 */
export class ListComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  projectListWidgets!: projectListModel[];
  projectListWidgets1!: projectListModel1[];
  projectListWidgets2!: projectListModel2[];
  projectmodel!: Observable<projectListModel2[]>;
  total: Observable<number>;
  sellers?: any;

  constructor(private modalService: NgbModal,
    public service: listService) {
    this.projectmodel = service.companies$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Projects' },
      { label: 'Project List', active: true }
    ];

    /**
     * Fetches the data
     */
    this.fetchData();
  }

  /**
   * Fetches the data
   */
  private fetchData() {
    // this.projectListWidgets = projectListWidgets;
    this.projectListWidgets1 = projectListWidgets1;
    this.projectListWidgets2 = projectListWidgets2;
    setTimeout(() => {
      this.projectmodel.subscribe(x => {
        this.projectListWidgets = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200);
  }

  /**
  * Confirmation mail model
  */
  deleteId: any;
  confirm(content: any, id: any) {
    this.deleteId = id;
    this.modalService.open(content, { centered: true });
  }

  // Delete Data
  deleteData(id: any) {
    document.getElementById('pl1_' + id)?.remove();
  }

  /**
   * Active Toggle navbar
   */
  activeMenu(id: any) {
    document.querySelector('.heart_icon_' + id)?.classList.toggle('active');
  }

}
