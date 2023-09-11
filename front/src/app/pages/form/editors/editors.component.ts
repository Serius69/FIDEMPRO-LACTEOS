import { Component, OnInit } from '@angular/core';

// Ck Editer
import * as ClassicEditor from '@ckeditor/ckeditor5-build-classic';

@Component({
  selector: 'app-editors',
  templateUrl: './editors.component.html',
  styleUrls: ['./editors.component.scss']
})

/**
 * Editors Component
 */
export class EditorsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  public Editor = ClassicEditor;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Forms' },
      { label: 'Editors', active: true }
    ];
  }

}
