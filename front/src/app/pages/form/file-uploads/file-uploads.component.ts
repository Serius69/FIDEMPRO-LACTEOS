import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-file-uploads',
  templateUrl: './file-uploads.component.html',
  styleUrls: ['./file-uploads.component.scss']
})

/**
 * FileUploads Component
 */
export class FileUploadsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Forms' },
      { label: 'File Upload', active: true }
    ];
  }

}
