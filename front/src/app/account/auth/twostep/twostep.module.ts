import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgbCarouselModule } from '@ng-bootstrap/ng-bootstrap';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

// otp module
import { NgOtpInputModule } from 'ng-otp-input';

// Component
import { TwoStepRoutingModule } from "./twostep-routing.module";
import { BasicComponent } from './basic/basic.component';
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
    NgOtpInputModule,
    TwoStepRoutingModule
  ]
})
export class TwostepModule { }
