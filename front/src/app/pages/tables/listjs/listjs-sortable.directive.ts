import {Directive, EventEmitter, Input, Output} from '@angular/core';
import {ListJsModel} from './listjs.model';

export type SortColumn = keyof ListJsModel | '';
export type SortDirection = 'asc' | 'desc' | '';
const rotate: {[key: string]: SortDirection} = { 'asc': 'desc', 'desc': '', '': 'asc' };

export interface listSortEvent {
  column: SortColumn;
  direction: SortDirection;
}

@Directive({
  selector: 'th[listsortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()'
  }
})
export class NgbdListSortableHeader {

  @Input() listsortable: SortColumn = '';
  @Input() direction: SortDirection = '';
  @Output() listsort = new EventEmitter<listSortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.listsort.emit({column: this.listsortable, direction: this.direction});
  }
}
