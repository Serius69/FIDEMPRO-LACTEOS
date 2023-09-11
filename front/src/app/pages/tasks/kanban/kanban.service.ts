import { Injectable, PipeTransform } from '@angular/core';
import { BehaviorSubject, Observable, of, Subject } from 'rxjs';

import { Task } from './kanban.model';
import { tasks } from './data';
import { DecimalPipe } from '@angular/common';
import { debounceTime, delay, switchMap, tap } from 'rxjs/operators';
// import {SortColumn, SortDirection} from './seller-details-sortable.directive';

interface SearchResult {
    companies: Task[];
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

const compare = (v1: string | number, v2: string | number) => v1 < v2 ? -1 : v1 > v2 ? 1 : 0;

function sort(companies: Task[]): Task[] {

    return companies;
}

function matches(company: Task, term: string, pipe: PipeTransform) {
    return company.title?.toLowerCase().includes(term.toLowerCase())
        || company.status.toLowerCase().includes(term.toLowerCase());
}

@Injectable({ providedIn: 'root' })
export class kanbanService {
    private _loading$ = new BehaviorSubject<boolean>(true);
    private _search$ = new Subject<void>();
    private _companies$ = new BehaviorSubject<Task[]>([]);
    private _total$ = new BehaviorSubject<number>(0);

    products: any | undefined;

    private _state: State = {
        page: 1,
        pageSize: 10,
        searchTerm: '',
        startIndex: 0,
        endIndex: 9,
        totalRecords: 0,
        category: '',
    };

    constructor(private pipe: DecimalPipe) {
        this._search$.pipe(
            tap(() => this._loading$.next(true)),
            debounceTime(200),
            switchMap(() => this._search()),
            delay(200),
            tap(() => this._loading$.next(false))
        ).subscribe(result => {
            this._companies$.next(result.companies);
            this._total$.next(result.total);
        });

        this._search$.next();

        // fetch Data
        this.products = tasks
    }

    get companies$() { return this._companies$.asObservable(); }
    get product() { return this.products; }
    get total$() { return this._total$.asObservable(); }
    get loading$() { return this._loading$.asObservable(); }
    get page() { return this._state.page; }
    get pageSize() { return this._state.pageSize; }
    get searchTerm() { return this._state.searchTerm; }
    get startIndex() { return this._state.startIndex; }
    get endIndex() { return this._state.endIndex; }
    get totalRecords() { return this._state.totalRecords; }
    get category() { return this._state.category; }

    set page(page: number) { this._set({ page }); }
    set pageSize(pageSize: number) { this._set({ pageSize }); }
    set searchTerm(searchTerm: string) { this._set({ searchTerm }); }
    set startIndex(startIndex: number) { this._set({ startIndex }); }
    set endIndex(endIndex: number) { this._set({ endIndex }); }
    set totalRecords(totalRecords: number) { this._set({ totalRecords }); }
    set category(category: any) { this._set({ category }); }

    private _set(patch: Partial<State>) {
        Object.assign(this._state, patch);
        this._search$.next();
    }

    private _search(): Observable<SearchResult> {
        const datas = (this.product) ?? [];
        const { pageSize, page, searchTerm, category } = this._state;

        // 1. sort
        let companies = sort(datas);


        // 2. filter
        companies = companies.filter(company => matches(company, searchTerm, this.pipe));
        const total = companies.length;

        // 5. Status Filter
        // if (category && category != 'All') {
        //     companies = companies.filter(company => company.category == category);
        // }
        // else {
        //     companies = companies;
        // }

        // 3. paginate
        this.totalRecords = companies.length;
        this._state.startIndex = (page - 1) * this.pageSize + 1;
        this._state.endIndex = (page - 1) * this.pageSize + this.pageSize;
        if (this.endIndex > this.totalRecords) {
            this.endIndex = this.totalRecords;
        }
        companies = companies.slice(this._state.startIndex - 1, this._state.endIndex);

        return of({ companies, total });
    }
}