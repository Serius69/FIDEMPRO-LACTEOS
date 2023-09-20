import { Injectable, PipeTransform } from '@angular/core';
import { BehaviorSubject, debounceTime, delay, Observable, of, Subject, switchMap, tap } from 'rxjs';
import { HttpClient, HttpParams } from '@angular/common/http';
import { DecimalPipe } from '@angular/common';
import { productListModel2 } from './list.model';

interface GetResponseProducts {
  products: productListModel2[];
  total: number;
}

interface State {
  page: number;
  pageSize: number;
  startIndex: number;
  endIndex: number;
  searchTerm: string;
  totalRecords: number;
  category: string;
}

@Injectable({ providedIn: 'root' })
export class ListService {
  // URL
  private baseUrl = 'http://localhost:8000/product';

  private _loading$ = new BehaviorSubject<boolean>(true);
  private _search$ = new Subject<void>();
  private _products$ = new BehaviorSubject<productListModel2[]>([]);
  private _total$ = new BehaviorSubject<number>(0);

  private _state: State = {
    page: 1,
    pageSize: 10,
    searchTerm: '',
    startIndex: 0,
    endIndex: 9,
    totalRecords: 0,
    category: '',
  };

  constructor(private pipe: DecimalPipe, private httpClient: HttpClient) {
    this._search$
      .pipe(
        tap(() => this._loading$.next(true)),
        debounceTime(200),
        switchMap(() => this._search()),
        delay(200),
        tap(() => this._loading$.next(false))
      )
      .subscribe((result) => {
        this._products$.next(result.products);
        this._total$.next(result.total);
      });

    this._search$.next();
  }

  get products$() {
    return this._products$.asObservable();
  }
  get total$() {
    return this._total$.asObservable();
  }
  get loading$() {
    return this._loading$.asObservable();
  }

  get page() {
    return this._state.page;
  }
  get pageSize() {
    return this._state.pageSize;
  }
  get searchTerm() {
    return this._state.searchTerm;
  }
  get startIndex() {
    return this._state.startIndex;
  }
  get endIndex() {
    return this._state.endIndex;
  }
  get totalRecords() {
    return this._state.totalRecords;
  }
  get category() {
    return this._state.category;
  }

  set page(page: number) {
    this._set({ page });
  }
  set pageSize(pageSize: number) {
    this._set({ pageSize });
  }
  set searchTerm(searchTerm: string) {
    this._set({ searchTerm });
  }
  set startIndex(startIndex: number) {
    this._set({ startIndex });
  }
  set endIndex(endIndex: number) {
    this._set({ endIndex });
  }
  set totalRecords(totalRecords: number) {
    this._set({ totalRecords });
  }
  set category(category: any) {
    this._set({ category });
  }

  private _set(patch: Partial<State>) {
    Object.assign(this._state, patch);
    this._search$.next();
  }

  private _search(): Observable<GetResponseProducts> {
    const { pageSize, page, searchTerm, category } = this._state;
    return this.httpClient.get<GetResponseProducts>(this.baseUrl, {
    //   params: {
    //     page: page.toString(),
    //     pageSize: pageSize.toString(),
    //     searchTerm,
    //     category,
    //   },
    });
  }
}
