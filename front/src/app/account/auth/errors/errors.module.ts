import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// Load Icons
import { defineElement  } from 'lord-icon-element';
import lottie from 'lottie-web';

// Component
import { Error404RoutingModule } from "./errors-routing.module";
import { CoverComponent } from './400/cover.component';
import { Page500Component } from './500/page500.component';
import { OfflineComponent } from './300/offline.component';

@NgModule({
  declarations: [
    CoverComponent,
    Page500Component,
    OfflineComponent
  ],
  imports: [
    CommonModule,
    Error404RoutingModule
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class ErrorsModule { 
  constructor() {
    defineElement (lottie.loadAnimation);
  }
}
