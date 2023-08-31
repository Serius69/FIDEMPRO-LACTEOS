import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class VariableService {
  private apiUrl = 'tu_url_api';

  constructor(private http: HttpClient) { }

  getVariables(): Observable<Variable[]> {
    return this.http.get<Variable[]>(`${this.apiUrl}/variables`);
  }

  updateVariable(variable: Variable): Observable<Variable> {
    return this.http.put<Variable>(`${this.apiUrl}/variables/${variable.id}`, variable);
  }

  deleteVariable(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/variables/${id}`);
  }
}
