import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Variable } from '../common/variable';

@Injectable({
  providedIn: 'root'
})
export class VariableService {
  private apiUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) { }

  getAll(): Observable<Variable[]> {
    return this.http.get<Variable[]>(`${this.apiUrl}/variables`);
  }

  create(variable: Variable): Observable<Variable> {
    return this.http.post<Variable>(`${this.apiUrl}/variables`, variable);
  }

  update(id: string, variable: Variable): Observable<Variable> {
    return this.http.put<Variable>(`${this.apiUrl}/variables/${id}`, variable);
  }

  delete(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/variables/${id}`);
  }
}
