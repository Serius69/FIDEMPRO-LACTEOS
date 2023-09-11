import { Component, OnInit } from '@angular/core';
import { UsersService } from "../../services/users.service";
@Component({
  selector: 'app-header',
  templateUrl: './header.component.html'
})
export class HeaderComponent implements OnInit {
  user: any; // Variable para almacenar los datos del usuario

  constructor(private userService: UsersService,) { }

  ngOnInit(): void {
    // En el método ngOnInit, puedes cargar los datos del usuario desde el servicio
    const userId = 1;
    this.userService.getUser(userId).subscribe((data) => {
      this.user = data; // Asigna los datos del usuario a la variable 'user'
    });
  }
}
