import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { UsersService } from '../../../services/users.service';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.component.html'
})
export class SignupComponent implements OnInit {

  signupForm = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    email: ['', [Validators.required, Validators.email]]
  });

  constructor(
    private fb: FormBuilder,
    private userService: UsersService
  ) {}

  ngOnInit() {}

  signup() {
    if (this.signupForm.invalid) {
      return;
    }
    
    const username = this.signupForm.value.username!;
    const password = this.signupForm.value.password!; 
    const email = this.signupForm.value.email!;

    this.userService.signup(username, password, email)
      .subscribe({
        next: () => {
          // redirect to confirmation
        },
        error: error => {
          // handle error
        }
      })
  }

}