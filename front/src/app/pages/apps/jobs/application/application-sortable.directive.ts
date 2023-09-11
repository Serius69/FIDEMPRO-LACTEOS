import { Directive, EventEmitter, Input, Output } from '@angular/core';
import { ApplicationModel } from './application.model';

export type SortColumn = keyof ApplicationModel | '';
export type SortDirection = 'asc' | 'desc' | '';
const rotate: { [key: string]: SortDirection } = { 'asc': 'desc', 'desc': '', '': 'asc' };

export interface appSortEvent {
  column: SortColumn;
  direction: SortDirection;
}

@Directive({
  selector: 'th[appsortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()'
  }
})
export class NgbdappSortableHeader {
  @Input() appsortable: SortColumn = '';
  @Input() direction: SortDirection = '';
  @Output() appsort = new EventEmitter<appSortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.appsort.emit({ column: this.appsortable, direction: this.direction });
  }
}
