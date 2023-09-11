import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, Validators, UntypedFormGroup, UntypedFormArray, AbstractControl } from '@angular/forms';

@Component({
  selector: 'app-newjob',
  templateUrl: './newjob.component.html',
  styleUrls: ['./newjob.component.scss']
})
export class NewjobComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  tags: any;
  // Form
  itemData!: UntypedFormGroup;
  submitted = false;

  constructor(public formBuilder: UntypedFormBuilder) { }

  ngOnInit(): void {
    /**
* BreadCrumb
*/
    this.breadCrumbItems = [
      { label: 'Jobs' },
      { label: 'New Job', active: true }
    ];

    // Validation
    this.itemData = this.formBuilder.group({
      title: ['', [Validators.required]],
      position: ['', [Validators.required]],
      category: ['', [Validators.required]],
      job_type: ['', [Validators.required]],
      description: ['', [Validators.required]],
      vacancy: ['', [Validators.required]],
      experience: ['', [Validators.required]],
      last_date: ['', [Validators.required]],
      close_date: ['', [Validators.required]],
      start_salary: ['', [Validators.required]],
      last_salary: ['', [Validators.required]],
      country: ['', [Validators.required]],
      state: ['', [Validators.required]],
      tags: ['', [Validators.required]],
    });

    /**
   * Default Select2
   */
    // multiDefaultOption1 = 'Watches';
    // Default1 = [
    //   { name: 'Watches' },
    //   { name: 'Headset' },
    //   { name: 'Sweatshirt' },
    // ];


  }

  /**
* Returns form
*/
  get form() {
    return this.itemData.controls;
  }

  createJob() {
    if (this.itemData.valid) {
    }
    this.submitted = true;
  }

}
