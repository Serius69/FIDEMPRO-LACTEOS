import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { first } from 'rxjs/operators';

import { RegisterService } from './register.service'; // Import your register service here

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html'
})
export class RegisterComponent implements OnInit {
  signupForm!: FormGroup;
  submitted = false;
  successmsg = false;
  error = '';
  year: number = new Date().getFullYear();

  constructor(
    private formBuilder: FormBuilder,
    private router: Router,
    private registerService: RegisterService, // Inject your register service here
  ) {}

  ngOnInit(): void {
    this.signupForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      name: ['', [Validators.required]],
      password: ['', Validators.required],
    });
  }

  get f() {
    return this.signupForm.controls;
  }

  onSubmit() {
    this.submitted = true;

    if (this.signupForm.invalid) {
      return;
    }

    const userData = {
      email: this.f['email'].value,
      name: this.f['name'].value,
      password: this.f['password'].value,
    };

    this.registerService.registerUser(userData).pipe(first()).subscribe(
      (data: any) => {
        this.successmsg = true;
        if (this.successmsg) {
          this.router.navigate(['/auth/login']);
        }
      },
      (error) => {
        this.error = error ? error : '';
      }
    );
  }
}
