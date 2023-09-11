import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// Load Icons
import { defineElement  } from 'lord-icon-element';
import lottie from 'lottie-web';

// Component
import { Error404RoutingModule } from "./errors-routing.module";
import { BasicComponent } from './basic/basic.component';
import { CoverComponent } from './cover/cover.component';
import { AltComponent } from './alt/alt.component';
import { Page500Component } from './page500/page500.component';
import { OfflineComponent } from './offline/offline.component';

@NgModule({
  declarations: [
    BasicComponent,
    CoverComponent,
    AltComponent,
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
