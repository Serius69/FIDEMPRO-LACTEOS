import { Component, OnInit } from '@angular/core';
import { UsersService } from "../users/users.service";
@Component({
  selector: 'app-header',
  templateUrl: './header.component.html'
})
export class HeaderComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

  getUserLogged() {
    this.userService.getUser().subscribe((user) => {
      console.log(user);
    });
  }
}
