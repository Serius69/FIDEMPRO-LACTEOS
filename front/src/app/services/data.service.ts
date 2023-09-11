import { Injectable } from '@angular/core';
import { FDP } from '../core/common/fdp';

@Injectable({
  providedIn: 'root',
})
export class DataService {
  private data: any[] = []; // Example data storage

  constructor() {}

  getData(): any[] {
    return this.data;
  }

  addData(item: any): void {
    this.data.push(item);
  }
}
