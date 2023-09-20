import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const baseUrl = 'http://localhost:8000/api/products'; // Update the base URL accordingly

@Injectable({
  providedIn: 'root'
})
export class AddService {

  constructor(private http: HttpClient) { }
 
  // Create a new product
  create(data: any): Observable<any> {
    return this.http.post(baseUrl, data);
  }

  // Update a product by ID
  update(id: string, data: any): Observable<any> {
    return this.http.put(`${baseUrl}/${id}`, data);
  }

  // Delete a product by ID
  delete(id: string): Observable<any> {
    return this.http.delete(`${baseUrl}/${id}`);
  }

  // Delete all products
  deleteAll(): Observable<any> {
    return this.http.delete(baseUrl);
  }
}