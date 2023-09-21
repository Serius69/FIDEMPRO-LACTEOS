import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
@Injectable({
  providedIn: 'root'
})
export class RegisterService {

  private apiUrl = 'http://localhost:8000/register/'; // Replace with your API URL

  constructor(private http: HttpClient) {}

  registerUser(userData: any): Observable<any> {
    const httpOptions = {
      headers: new HttpHeaders({ 'Content-Type': 'application/json' }),
    };

    return this.http
      .post<any>(this.apiUrl, userData, httpOptions)
      .pipe(catchError(this.handleError));
  }

  private handleError(error: any) {
    // Add your error handling logic here
    console.error('An error occurred:', error);
    return throwError(error);
  }
}
