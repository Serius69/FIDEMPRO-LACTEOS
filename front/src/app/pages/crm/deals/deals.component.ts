import { Component, OnInit } from '@angular/core';

import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'app-deals',
  templateUrl: './deals.component.html',
  styleUrls: ['./deals.component.scss']
})

/**
 * Deals Component
 */
export class DealsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  submitted = false;

  constructor(private modalService: NgbModal) { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'CRM' },
      { label: 'Deals', active: true }
    ];
  }

  /**
   * Open modal
   * @param content modal content
   */
   openModal(content: any) {
    this.submitted = false;
    this.modalService.open(content, { size: 'md', centered: true });
  }

}
