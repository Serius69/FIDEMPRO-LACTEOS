import {Directive, EventEmitter, Input, Output} from '@angular/core';
import { Variable } from 'src/app/core/common/variable';

export type SortColumn = keyof Variable | '';
export type SortDirection = 'asc' | 'desc' | '';
const rotate: {[key: string]: SortDirection} = { 'asc': 'desc', 'desc': '', '': 'asc' };

export interface variableSortEvent {
  column: SortColumn;
  direction: SortDirection;
}

@Directive({
  selector: 'th[productsortable]',
  host: {
    '[class.asc]': 'direction === "asc"',
    '[class.desc]': 'direction === "desc"',
    '(click)': 'rotate()'
  }
})
export class NgbdProductsSortableHeader {

  @Input() productsortable: SortColumn = '';
  @Input() direction: SortDirection = '';
  @Output() productsort = new EventEmitter<variableSortEvent>();

  rotate() {
    this.direction = rotate[this.direction];
    this.productsort.emit({column: this.productsortable, direction: this.direction});
  }
}
