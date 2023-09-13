import { Component } from '@angular/core';

// Ck Editer
import * as ClassicEditor from '@ckeditor/ckeditor5-build-classic';

@Component({
  selector: 'app-add',
  templateUrl: './add.component.html',
  styleUrls: ['./add.component.scss']
})
export class AddComponent {
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
