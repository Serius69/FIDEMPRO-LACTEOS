import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BasicComponent } from './basic/basic.component';

import { NgbCarouselModule } from '@ng-bootstrap/ng-bootstrap';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

// Component
import { SigninRoutingModule } from './signup-routing.module';
import { CoverComponent } from './cover/cover.component';

@NgModule({
  declarations: [
    BasicComponent,
    CoverComponent
  ],
  imports: [
    CommonModule,
    NgbCarouselModule,
    ReactiveFormsModule,
    FormsModule,
    SigninRoutingModule
  ]
})
export class SignupModule { }
