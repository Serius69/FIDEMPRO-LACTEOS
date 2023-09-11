/* eslint-disable @typescript-eslint/adjacent-overload-signatures */
import {Injectable, PipeTransform} from '@angular/core';

import {BehaviorSubject, Observable, of, Subject} from 'rxjs';

import {LeadsModel} from './leads.model';
import {Leads} from './data';
import {DecimalPipe} from '@angular/common';
import {debounceTime, delay, switchMap, tap} from 'rxjs/operators';
import {SortColumn, SortDirection} from './leads-sortable.directive';

// Products Services
import { restApiService } from "../../../core/services/rest-api.service";

interface SearchResult {
  leads: LeadsModel[];
  total: number;
}

interface State {
  page: number;
  pageSize: number;
  searchTerm: string;
  sortColumn: SortColumn;
  sortDirection: SortDirection;
  startIndex: number;
  endIndex: number;
  totalRecords: number;
}

const compare = (v1: string | number, v2: string | number) => v1 < v2 ? -1 : v1 > v2 ? 1 : 0;

function sort(leads: LeadsModel[], column: SortColumn, direction: string): LeadsModel[] {
  if (direction === '' || column === '') {
    return leads;
  } else {
    return [...leads].sort((a, b) => {
      const res = compare(a[column], b[column]);
      return direction === 'asc' ? res : -res;
    });
  }
}

function matches(country: LeadsModel, term: string, pipe: PipeTransform) {
  return country.name.toLowerCase().includes(term.toLowerCase())
  ;
}

@Injectable({providedIn: 'root'})
export class LeadsService {
  private _loading$ = new BehaviorSubject<boolean>(true);
  private _search$ = new Subject<void>();
  private _leads$ = new BehaviorSubject<LeadsModel[]>([]);
  private _total$ = new BehaviorSubject<number>(0);

  leads?: any;

  private _state: State = {
    page: 1,
    pageSize: 8,
    searchTerm: '',
    sortColumn: '',
    sortDirection: '',
    startIndex: 0,
    endIndex: 9,
    totalRecords: 0
  };

  constructor(private pipe: DecimalPipe, public restApiService: restApiService) {
    this._search$.pipe(
      tap(() => this._loading$.next(true)),
      debounceTime(200),
      switchMap(() => this._search()),
      delay(200),
      tap(() => this._loading$.next(false))
    ).subscribe(result => {
      this._leads$.next(result.leads);
      this._total$.next(result.total);
    });

    this._search$.next();

    // Api Data
    this.restApiService.getLeadData().subscribe(
      data => {        
        const users =  JSON.parse(data);
        this.leads = users.data;
    });

  }

  get leads$() { return this._leads$.asObservable(); }
  get datas() { return this.leads; }
  get total$() { return this._total$.asObservable(); }
  get loading$() { return this._loading$.asObservable(); }
  get page() { return this._state.page; }
  get pageSize() { return this._state.pageSize; }
  get searchTerm() { return this._state.searchTerm; }
  get startIndex() { return this._state.startIndex; }
  get endIndex() { return this._state.endIndex; }
  get totalRecords() { return this._state.totalRecords; }

  set page(page: number) { this._set({page}); }
  set pageSize(pageSize: number) { this._set({pageSize}); }
  set searchTerm(searchTerm: string) { this._set({searchTerm}); }
  set sortColumn(sortColumn: SortColumn) { this._set({sortColumn}); }
  set sortDirection(sortDirection: SortDirection) { this._set({sortDirection}); }
  set startIndex(startIndex: number) { this._set({ startIndex }); }
  set endIndex(endIndex: number) { this._set({ endIndex }); }
  set totalRecords(totalRecords: number) { this._set({ totalRecords }); }

  private _set(patch: Partial<State>) {
    Object.assign(this._state, patch);
    this._search$.next();
  }

  private _search(): Observable<SearchResult> {
    const datas = (this.datas) ?? [];
    const {sortColumn, sortDirection, pageSize, page, searchTerm} = this._state;

    // 1. sort
    let leads = sort(datas, sortColumn, sortDirection);

    // 2. filter
    leads = leads.filter(country => matches(country, searchTerm, this.pipe));
    const total = leads.length;

    // 3. paginate
    this.totalRecords = leads.length;
    this._state.startIndex = (page - 1) * this.pageSize + 1;
    this._state.endIndex = (page - 1) * this.pageSize + this.pageSize;
    if (this.endIndex > this.totalRecords) {
        this.endIndex = this.totalRecords;
    }
    leads = leads.slice(this._state.startIndex - 1, this._state.endIndex);
    return of({leads, total});
  }
}
