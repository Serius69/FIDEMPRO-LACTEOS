import { Component, OnInit } from '@angular/core';

// Ck Editer
import * as ClassicEditor from '@ckeditor/ckeditor5-build-classic';

@Component({
  selector: 'app-create',
  templateUrl: './create.component.html',
  styleUrls: ['./create.component.scss']
})

/**
 * Create Component
 */
export class CreateComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  public Editor = ClassicEditor;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Projects' },
      { label: 'Create Project', active: true }
    ];
  }

  /**
  * Multiple Default Select2
  */
   selectValue = ['Choice 1', 'Choice 2', 'Choice 3'];

}
