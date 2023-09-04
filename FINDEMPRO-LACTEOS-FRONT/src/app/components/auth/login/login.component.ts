import { Component, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { AuthService } from '../../../services/auth.service';
import { Router } from '@angular/router'; // Import Router

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html'
})
export class LoginComponent implements OnInit {

  loginForm = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', [Validators.required, Validators.minLength(6)]]
  });

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router // Inject Router
  ) {}

  ngOnInit() {}

  login() {
    if (this.loginForm.invalid) {
      return;
    }

    const usernameControl = this.loginForm.get('username');
    const username = usernameControl ? usernameControl.value : null;
    const passwordControl = this.loginForm.get('password');
    const password = passwordControl ? passwordControl.value : null;    
    
    this.authService.login(username, password)
      .subscribe({
        next: () => {
          this.router.navigate(['/home']); // Redirect to home page
        },
        error: (error: any) => {
          console.error(error); // Log the error for debugging
          // Display an error message to the user
        }
      });
  }

}
