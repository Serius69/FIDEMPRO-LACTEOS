import { Component, QueryList, ViewChildren, OnInit } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { NgbModal, NgbNavChangeEvent } from '@ng-bootstrap/ng-bootstrap';
import { Observable } from 'rxjs';
import { UntypedFormBuilder, Validators, UntypedFormGroup, UntypedFormArray, AbstractControl } from '@angular/forms';

import { application } from './data';
import { ApplicationModel } from './application.model';
import { ApplicationService } from './application.service';
import { NgbdappSortableHeader, appSortEvent } from './application-sortable.directive';
// Sweet Alert
import Swal from 'sweetalert2';

@Component({
  selector: 'app-application',
  templateUrl: './application.component.html',
  styleUrls: ['./application.component.scss'],
  providers: [ApplicationService, DecimalPipe]
})
export class ApplicationComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  applications: any;
  masterSelected!: boolean;
  @ViewChildren(NgbdappSortableHeader) headers!: QueryList<NgbdappSortableHeader>;
  // Form
  applicationData!: UntypedFormGroup;
  submitted = false;

  // Table data
  Applicationlist!: Observable<ApplicationModel[]>;
  total: Observable<number>;

  constructor(public service: ApplicationService,
    public formBuilder: UntypedFormBuilder,
    public modalService: NgbModal) {
    this.Applicationlist = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
* BreadCrumb
*/
    this.breadCrumbItems = [
      { label: 'Jobs' },
      { label: 'Application', active: true }
    ];

    // Validation
    this.applicationData = this.formBuilder.group({
      id: [''],
      name: ['', [Validators.required]],
      date: ['', [Validators.required]],
      type: ['', [Validators.required]],
      designation: ['', [Validators.required]],
      contacts: ['', [Validators.required]],
      status: ['', [Validators.required]]
    });

    // Fetch Data
    setTimeout(() => {
      this.Applicationlist.subscribe(x => {
        this.applications = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200)
  }

  onNavChange(changeEvent: NgbNavChangeEvent) {
    if (changeEvent.nextId === 1) {
      this.service.searchTerm = ''
    }
    if (changeEvent.nextId === 2) {
      this.service.searchTerm = 'New'
    }
    if (changeEvent.nextId === 3) {
      this.service.searchTerm = 'Pending'
    }
    if (changeEvent.nextId === 4) {
      this.service.searchTerm = 'Approved'
    }
    if (changeEvent.nextId === 5) {
      this.service.searchTerm = 'Rejected'
    }
  }

  // Check Box Checked Value Get
  checkedValGet: any[] = [];
  // The master checkbox will check/ uncheck all items
  checkUncheckAll(ev: any) {
    this.applications.forEach((x: { state: any; }) => x.state = ev.target.checked)
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.applications.length; i++) {
      if (this.applications[i].state == true) {
        result = this.applications[i].id;
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";

  }
  isAllChecked() {
    return this.applications.every((_: { state: any; }) => _.state);
  }

  // Select Checkbox value Get
  onCheckboxChange(e: any) {
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.applications.length; i++) {
      if (this.applications[i].state == true) {
        result = this.applications[i].id;
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";
  }

  // Open add Model
  openModel(content: any) {
    this.modalService.open(content, { size: 'md', centered: true });
  }

  // File Upload
  imageURL: string | undefined;
  fileChange(event: any) {
    let fileList: any = (event.target as HTMLInputElement);
    let file: File = fileList.files[0];
    const reader = new FileReader();
    reader.onload = () => {
      this.imageURL = reader.result as string;
      document.querySelectorAll('#companylogo-img').forEach((element: any) => {
        element.src = this.imageURL;
      });
    }
    reader.readAsDataURL(file)
  }

  /**
  * Open modal
  * @param content modal content
  */
  singleData: any;
  editorder(content: any, id: any) {
    this.singleData = this.applications[id];
    this.submitted = false;
    this.modalService.open(content, { size: ' md', centered: true })
    var modelTitle = document.querySelector('.modal-title') as HTMLAreaElement;
    modelTitle.innerHTML = 'Edit Application';
    var updatebtn = document.getElementById('add-btn') as HTMLAreaElement
    updatebtn.innerHTML = "Update";
    document.querySelectorAll('#companylogo-img').forEach((element: any) => {
      element.src = this.singleData.img;
    });
    this.applicationData.controls['id'].setValue(this.singleData.id);
    this.applicationData.controls['name'].setValue(this.singleData.name);
    this.applicationData.controls['designation'].setValue(this.singleData.designation);
    this.applicationData.controls['date'].setValue(this.singleData.date);
    this.applicationData.controls['contacts'].setValue(this.singleData.contacts);
    this.applicationData.controls['type'].setValue(this.singleData.type);
    this.applicationData.controls['status'].setValue(this.singleData.status);
  }

  /**
* Returns form
*/
  get form() {
    return this.applicationData.controls;
  }

  createapplication() {
    if (this.applicationData.valid) {
      if (this.applicationData.get('id')?.value) {
        this.service.products = this.applications.map((data: { id: any; }) => data.id === this.applicationData.get('id')?.value ? { ...data, ...this.applicationData.value } : data)
        // this.service.products = this.applications
      } else {
        const name = this.applicationData.get('name')?.value;
        const designation = this.applicationData.get('designation')?.value;
        const contacts = this.applicationData.get('contacts')?.value;
        const img = "/assets/images/brands/slack.png";
        const date = '26 Sep, 2022';
        const status = this.applicationData.get('status')?.value;
        const type = this.applicationData.get('type')?.value;
        this.service.products.push({
          id: this.applications.length + 1,
          img,
          name,
          designation,
          date,
          contacts,
          type,
          status
        });
        this.modalService.dismissAll()
      }
    }
    this.modalService.dismissAll();
    setTimeout(() => {
      this.applicationData.reset();
    }, 2000);
    this.submitted = true
  }

  /**
   * Delete Model Open
   */
  deleteId: any;
  confirm(content: any, id: any) {
    this.deleteId = id;
    this.modalService.open(content, { centered: true });
  }

  // Delete Data
  deleteData(id: any) {
    if (id) {
      document.getElementById('a_' + id)?.remove();
    }
    this.checkedValGet.forEach((item: any) => {
      document.getElementById('a_' + item)?.remove();
      this.masterSelected = false;
    });
    this.modalService.dismissAll('close click')
    let timerInterval: any;
    Swal.fire({
      title: 'Deleted!',
      text: 'Your data has been deleted.',
      icon: 'success',
      confirmButtonColor: '#299cdb',
      timer: 2000,
      timerProgressBar: true,
      willClose: () => {
        clearInterval(timerInterval);
      },
    });
  }

  /**
* Sort table data
* @param param0 sort the column
*
*/
  onSort({ column, direction }: appSortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.appsortable !== column) {
        header.direction = '';
      }
    });
    this.service.sortColumn = column;
    this.service.sortDirection = direction;
  }
}
