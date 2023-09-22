// import { Injectable } from '@angular/core';
// import { HttpClient, HttpHeaders } from '@angular/common/http';
// import { Observable } from 'rxjs';

// @Injectable({
//   providedIn: 'root'
// })
// export class LoginService {
//   private djangoAuthUrl = 'http://localhost:8000/api-user-login/'; // Reemplaza con la URL correcta de autenticación en Django

//   constructor(private http: HttpClient) { }

//   login(username: string, password: string): Observable<any> {
//     const body = {
//       username: username,
//       password: password
//     };

//     const httpOptions = {
//       headers: new HttpHeaders({
//         'Content-Type': 'application/json'
//       })
//     };

//     return this.http.post(this.djangoAuthUrl, body, httpOptions);
//   }
// }
