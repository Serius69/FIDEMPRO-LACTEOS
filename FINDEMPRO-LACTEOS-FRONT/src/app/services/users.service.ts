import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { CookieService } from "ngx-cookie-service";
import { User } from "../common/user"; // Asegúrate de importar la clase User si es necesario

@Injectable({
  providedIn: "root",
})
export class UsersService {
  private apiUrl = 'https://127/usuarios'; // Corrige la URL de tu API aquí

  constructor(private http: HttpClient, private cookies: CookieService) {}

  login(username: string, password: string): Observable<any> {
    const user = { username, password };
    return this.http.post("https://reqres.in/api/login", user);
  }

  signup(username: string, password: string, email: string): Observable<any> {
    const user = { username, password, email };
    return this.http.post("https://reqres.in/api/register", user);
  }

  setToken(token: string) {
    this.cookies.set("token", token);
  }

  getToken() {
    return this.cookies.get("token");
  }

  getUser(id: number): Observable<User> {
    // Usa la URL correcta de tu API y agrega /id al final
    return this.http.get<User>(`${this.apiUrl}/${id}`);
  }

  getUserLogged(): Observable<User> {
    const token = this.getToken();
    // Aquí deberías hacer una solicitud para obtener el usuario actual basado en el token
    // Ejemplo:
    return this.http.get<User>(`${this.apiUrl}/usuario-actual`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  updateUser(id: number, userData: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}`, userData);
  }

  deleteUser(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`);
  }
}
