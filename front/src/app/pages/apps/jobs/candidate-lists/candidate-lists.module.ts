import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgbPaginationModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';


// Routing
import { CandidateListsRoutingModule } from './candidate-lists-routing.module';
import { SharedModule } from 'src/app/shared/shared.module';

import { ListViewComponent } from './list-view/list-view.component';
import { GridViewComponent } from './grid-view/grid-view.component';



@NgModule({
  declarations: [
    ListViewComponent,
    GridViewComponent
  ],
  imports: [
    CommonModule,
    CandidateListsRoutingModule,
    SharedModule,
    NgbPaginationModule,
    FormsModule,
    ReactiveFormsModule
  ]
})
export class CandidateListsModule { }
