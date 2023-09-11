import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgbCarouselModule } from '@ng-bootstrap/ng-bootstrap';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

// Load Icons
import { defineElement  } from 'lord-icon-element';
import lottie from 'lottie-web';

// Component
import { LogoutRoutingModule } from './logout-routing.module';
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
    LogoutRoutingModule
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class LogoutModule { 
  constructor() {
    defineElement(lottie.loadAnimation);
  }
}
