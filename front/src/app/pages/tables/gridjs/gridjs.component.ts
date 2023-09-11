import {Component, QueryList, ViewChildren} from '@angular/core';
import {DecimalPipe} from '@angular/common';
import {Observable} from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';

import {GridJsModel} from './gridjs.model';
import { GridJs } from './data';
import { GridJsService } from './gridjs.service';
import { NgbdGridJsSortableHeader, SortEvent } from './gridjs-sortable.directive';

@Component({
  selector: 'app-gridjs',
  templateUrl: './gridjs.component.html',
  styleUrls: ['./gridjs.component.scss'],
  providers: [GridJsService, DecimalPipe]
})

/**
 * Gridjs Table Component
 */
export class GridjsComponent {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  // Table data
  gridjsList$!: Observable<GridJsModel[]>;
  total$: Observable<number>;
  @ViewChildren(NgbdGridJsSortableHeader) headers!: QueryList<NgbdGridJsSortableHeader>;

  constructor(private modalService: NgbModal,public service: GridJsService, private formBuilder: UntypedFormBuilder) {
    this.gridjsList$ = service.countries$;
    this.total$ = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Tables' },
      { label: 'Grid Js', active: true }
    ];
  }

  /**
  * Sort table data
  * @param param0 sort the column
  *
  */
   onSort({column, direction}: SortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    this.service.sortColumn = column;
    this.service.sortDirection = direction;
  }

}
