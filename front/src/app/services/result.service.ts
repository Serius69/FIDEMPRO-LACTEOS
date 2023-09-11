import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { DataNumber } from 'src/app/common/result';
import { DataStringNumber } from 'src/app/common/result';
import { DataStringStringNumber } from 'src/app/common/result';

@Injectable({
  providedIn: 'root'
})
export class ResultService {

  private baseUrl = 'http://127.0.0.1:8000/api';
  constructor(private httpClient: HttpClient) { }

  getEarnings(): Observable<DataNumber> {
    // need to build URL based on dashboard URL
    const dashboardUrl = `${this.baseUrl}/getearnings`;
    console.log("result getEarnings");
    return this.httpClient.get<DataNumber>(dashboardUrl);
  }
  getSales(): Observable<DataNumber> {
    // need to build URL based on dashboard URL
    const dashboardUrl = `${this.baseUrl}/getsales`;
    console.log("result getSales");
    return this.httpClient.get<DataNumber>(dashboardUrl);
  }
  getProfit(): Observable<DataNumber> {
    // need to build URL based on dashboard URL
    const dashboardUrl = `${this.baseUrl}/getprofit`;
    console.log("result getProfit");
    return this.httpClient.get<DataNumber>(dashboardUrl);
  }
  getExpenses(): Observable<DataNumber> {
    // need to build URL based on dashboard URL
    const dashboardUrl = `${this.baseUrl}/getexpenses`;
    console.log("result getExpenses");
    return this.httpClient.get<DataNumber>(dashboardUrl);
  }



}
