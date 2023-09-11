import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const baseUrl = 'http://localhost:8000/api'; // Update the base URL accordingly

@Injectable({
  providedIn: 'root'
})
export class ProductService {

  constructor(private http: HttpClient) { }

  // Get all products
  getAll(): Observable<any> {
    return this.http.get(baseUrl);
  }

  // Get a product by ID
  get(id: string): Observable<any> {
    return this.http.get(`${baseUrl}/${id}`);
  }

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

  // Find products by title
  findByTitle(title: string): Observable<any> {
    return this.http.get(`${baseUrl}?title=${title}`);
  }
}
