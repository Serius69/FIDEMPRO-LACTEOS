import {Directive, EventEmitter, Input, Output} from '@angular/core';
import {CompaniesModel} from './companies.model';

export type SortColumn = keyof CompaniesModel | '';
export type SortDirection = 'asc' | 'desc' | '';
const rotate: {[key: string]: SortDirection} = { 'asc': 'desc', 'desc': '', '': 'asc' };

export interface companySortEvent {
  column: SortColumn;
  direction: SortDirection;
}

@Directive({
  selector: 'th[companiesortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()'
  }
})
export class NgbdCompaniesSortableHeader {

  @Input() companiesortable: SortColumn = '';
  @Input() direction: SortDirection = '';
  @Output() companysort = new EventEmitter<companySortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.companysort.emit({column: this.companiesortable, direction: this.direction});
  }
}
