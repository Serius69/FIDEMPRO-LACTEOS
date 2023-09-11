import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-validation',
  templateUrl: './validation.component.html',
  styleUrls: ['./validation.component.scss']
})

/**
 * Validation Component
 */
export class ValidationComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  //  Validation form
  validationform!: UntypedFormGroup;
  tooltipvalidationform!: UntypedFormGroup;
  submit!: boolean;
  formsubmit!: boolean;

  constructor(private formBuilder: UntypedFormBuilder) { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Forms' },
      { label: 'Forms Validation', active: true }
    ];

    /**
     * Bootstrap validation form data
     */
     this.validationform = this.formBuilder.group({
      firstName: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      lastName: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      username: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      city: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      state: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      zip: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      agree: ['', [Validators.required]],
    });

    /**
     * Bootstrap tooltip validation form data
     */
     this.tooltipvalidationform = this.formBuilder.group({
      firstName: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      lastName: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      userName: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      city: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      state: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
      zip: ['', [Validators.required, Validators.pattern('[a-zA-Z0-9]+')]],
    });

  }

  /**
  * Bootsrap validation form submit method
  */
   validSubmit() {
    this.submit = true;
  }

  /**
   * Returns form
   */
   get form() {
    return this.validationform.controls;
  }

  /**
   * Bootstrap tooltip form validation submit method
   */
   formSubmit() {
    this.formsubmit = true;
  }

  /**
   * returns tooltip validation form
   */
  get formData() {
    return this.tooltipvalidationform.controls;
  }

  /**
   * Show Code Toggle
   */
   ShowCode(event: any) {     
    let card = event.target.closest('.card');
    const preview = card.children[1].children[1];
    const codeView = card.children[1].children[2];
    if(codeView != null){
      codeView.classList.toggle('d-none');
    }
    if(preview != null){
      preview.classList.toggle('d-none');
      
    }
  }

}
