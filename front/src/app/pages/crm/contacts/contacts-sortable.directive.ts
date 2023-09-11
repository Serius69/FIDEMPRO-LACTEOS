import {Directive, EventEmitter, Input, Output} from '@angular/core';
import {ContactsModel} from './contacts.model';

export type SortColumn = keyof ContactsModel | '';
export type SortDirection = 'asc' | 'desc' | '';
const rotate: {[key: string]: SortDirection} = { 'asc': 'desc', 'desc': '', '': 'asc' };

export interface contactSortEvent {
  column: SortColumn;
  direction: SortDirection;
}

@Directive({
  selector: 'th[contactsortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()'
  }
})
export class NgbdContactsSortableHeader {

  @Input() contactsortable: SortColumn = '';
  @Input() direction: SortDirection = '';
  @Output() contactsort = new EventEmitter<contactSortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.contactsort.emit({column: this.contactsortable, direction: this.direction});
  }
}
