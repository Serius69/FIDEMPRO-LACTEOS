import {Directive, EventEmitter, Input, Output} from '@angular/core';
import {LeadsModel} from './leads.model';

export type SortColumn = keyof LeadsModel | '';
export type SortDirection = 'asc' | 'desc' | '';
const rotate: {[key: string]: SortDirection} = { 'asc': 'desc', 'desc': '', '': 'asc' };

export interface leadSortEvent {
  column: SortColumn;
  direction: SortDirection;
}

@Directive({
  selector: 'th[leadsortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()'
  }
})
export class NgbdLeadsSortableHeader {

  @Input() leadsortable: SortColumn = '';
  @Input() direction: SortDirection = '';
  @Output() leadsort = new EventEmitter<leadSortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.leadsort.emit({column: this.leadsortable, direction: this.direction});
  }
}
