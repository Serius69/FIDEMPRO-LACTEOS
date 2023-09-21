import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthenticationService } from 'src/app/core/services/auth.service';
import { ToastService } from './toast-service';
import { LoginService } from './login.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent implements OnInit {
  loginForm!: FormGroup;
  submitted = false;
  fieldTextType = false;
  error = '';

  constructor(
    private formBuilder: FormBuilder,
    private authenticationService: AuthenticationService,
    private router: Router,
    public toastService: ToastService,
    private loginService: LoginService
  ) {
    // Redirect to home if already logged in
    if (this.authenticationService.currentUserValue) {
      this.router.navigate(['/']);
    }
  }

  ngOnInit(): void {
    if (localStorage.getItem('currentUser')) {
      this.router.navigate(['/']);
    }

    // Form Validation
    this.loginForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]],
    });
  }

  // Convenience getter for easy access to form fields
  get f() { return this.loginForm.controls; }

  // Form submit
  onSubmit() {
    this.submitted = true;
  
    const username = this.f['email'].value;
    const password = this.f['password'].value;
  
    this.loginService.login(username, password).subscribe(
      (data: any) => {
        if (data.token) {
          localStorage.setItem('toast', 'true');
          localStorage.setItem('currentUser', JSON.stringify(data.data));
          localStorage.setItem('token', data.token);
          this.router.navigate(['/']);
        } else {
          this.toastService.show(data.message, { classname: 'bg-danger text-white', delay: 15000 });
        }
      },
      (error) => {
        console.error('Error:', error);
      }
    );
  }

  // Password Hide/Show
  toggleFieldTextType() {
    this.fieldTextType = !this.fieldTextType;
  }
}
