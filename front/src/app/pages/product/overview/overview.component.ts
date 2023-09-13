import {Component, QueryList, ViewChildren} from '@angular/core';
import {DecimalPipe} from '@angular/common';
import {Observable} from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

import { projectListWidgets } from './data';
import { projectListModel, TeamModel } from './overview.model';
import { TeamService } from './overview.service';
import { NgbdTeamSortableHeader, SortEvent } from './overview-sortable.directive';

@Component({
  selector: 'app-overview',
  templateUrl: './overview.component.html',
  styleUrls: ['./overview.component.scss'],
  providers: [TeamService, DecimalPipe]
})

/**
 * Overview Component
 */
export class OverviewComponent {

  projectListWidgets!: projectListModel[];
  submitted = false;

  // Table data
  teamOverviewList$!: Observable<TeamModel[]>;
  total$: Observable<number>;
  @ViewChildren(NgbdTeamSortableHeader) headers!: QueryList<NgbdTeamSortableHeader>;

  constructor(private modalService: NgbModal,public service: TeamService) {
    this.teamOverviewList$ = service.countries$;
    this.total$ = service.total$;
  }

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
    this.projectListWidgets = projectListWidgets;
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

    /**
   * Open modal
   * @param content modal content
   */
     openModal(content: any) {
      this.submitted = false;
      this.modalService.open(content, { size: 'md', centered: true });
    }

   /**
   * Active Toggle navbar
   */
  activeMenu(id:any) {            
    document.querySelector('.star_'+id)?.classList.toggle('active');
  }


}
