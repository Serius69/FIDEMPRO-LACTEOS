import { Component, OnInit } from '@angular/core';
// import { UsersService } from "../../services/users.service";
@Component({
  selector: 'app-header',
  templateUrl: './header.component.html'
})
export class HeaderComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

  // getUserLogged() {
  //   this.userService.getUser().subscribe((user) => {
  //     console.log(user);
  //   });
  // }
}
