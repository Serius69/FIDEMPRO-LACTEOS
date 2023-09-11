import { Component, QueryList, ViewChildren, OnInit } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, UntypedFormGroup, UntypedFormArray, UntypedFormControl, Validators } from '@angular/forms';

// Date Format
import { DatePipe } from '@angular/common';
// Csv File Export
import { ngxCsv } from 'ngx-csv/ngx-csv';

// Rest Api Service
import { restApiService } from "../../../core/services/rest-api.service";
import { GlobalComponent } from '../../../global-component';

// Sweet Alert
import Swal from 'sweetalert2';

import { ContactsModel } from './contacts.model';
import { Contacts } from './data';
import { ContactsService } from './contacts.service';
import { NgbdContactsSortableHeader, contactSortEvent } from './contacts-sortable.directive';

@Component({
  selector: 'app-contacts',
  templateUrl: './contacts.component.html',
  styleUrls: ['./contacts.component.scss'],
  providers: [ContactsService, DecimalPipe]
})

/**
 * Contacts Component
 */
export class ContactsComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  submitted = false;
  contactsForm!: UntypedFormGroup;
  CustomersData!: ContactsModel[];
  masterSelected!: boolean;
  checkedList: any;

  // Api Data
  content?: any;
  contacts?: any;
  econtent?: any;
  url = GlobalComponent.API_URL;

  // Table data
  contactsList!: Observable<ContactsModel[]>;
  total: Observable<number>;
  @ViewChildren(NgbdContactsSortableHeader) headers!: QueryList<NgbdContactsSortableHeader>;

  constructor(private modalService: NgbModal, public service: ContactsService, private formBuilder: UntypedFormBuilder, private restApiService: restApiService, private datePipe: DatePipe) {
    this.contactsList = service.contacts$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'CRM' },
      { label: 'Contacts', active: true }
    ];

    /**
     * Form Validation
     */
    this.contactsForm = this.formBuilder.group({
      image_src: ['avatar-8.jpg'],
      ids: [''],
      name: ['', [Validators.required]],
      company: ['', [Validators.required]],
      designation: ['', [Validators.required]],
      email: ['', [Validators.required]],
      phone: ['', [Validators.required]],
      lead_score: ['', [Validators.required]],
      tags: ['', [Validators.required]],
      last_contacted: ['', [Validators.required]],
      subItem: this.formBuilder.array([]),
    });

    /**
     * fetches data
     */
    setTimeout(() => {
      this.contactsList.subscribe(x => {
        this.content = this.contacts;
        this.contacts = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200);

  }

  /**
   * Open modal
   * @param content modal content
   */
  openModal(content: any) {
    this.submitted = false;
    this.modalService.open(content, { size: 'md', centered: true });
  }

  /**
  * Form data get
  */
  get form() {
    return this.contactsForm.controls;
  }

  // File Upload
  imageURL: string | undefined;
  fileChange(event: any) {
    let fileList: any = (event.target as HTMLInputElement);
    let file: File = fileList.files[0];
    document.getElementById('')
    this.contactsForm.patchValue({
      // image_src: file.name
      image_src: 'avatar-8.jpg'
    });
    const reader = new FileReader();
    reader.onload = () => {
      this.imageURL = reader.result as string;
      (document.getElementById('customer-img') as HTMLImageElement).src = this.imageURL;
    }
    reader.readAsDataURL(file)
  }

  /**
  * Save user
  */
  saveUser() {
    if (this.contactsForm.valid) {
      if (this.contactsForm.get('ids')?.value) {
        this.restApiService.patchContactData(this.contactsForm.value).subscribe(
          (data: any) => {
            this.service.contacts = this.content.map((order: { _id: any; }) => order._id === data.data.ids ? { ...order, ...data.data } : order);
            this.modalService.dismissAll();
          }
        )
      }
      else {
        this.restApiService.postContactData(this.contactsForm.value).subscribe(
          (data: any) => {
            this.service.contacts.push(data.data);
            this.modalService.dismissAll();
            let timerInterval: any;
            Swal.fire({
              title: 'Contact inserted successfully!',
              icon: 'success',
              timer: 2000,
              timerProgressBar: true,
              willClose: () => {
                clearInterval(timerInterval);
              },
            }).then((result) => {
              if (result.dismiss === Swal.DismissReason.timer) {
              }
            });
          },)
      }
    }
    setTimeout(() => {
      this.contactsForm.reset();
    }, 2000);
    this.submitted = true
  }

  /**
   * Open Edit modal
   * @param content modal content
   */
  editDataGet(id: any, content: any) {
    this.submitted = false;
    this.modalService.open(content, { size: 'md', centered: true });
    var modelTitle = document.querySelector('.modal-title') as HTMLAreaElement;
    modelTitle.innerHTML = 'Edit Contact';
    var updateBtn = document.getElementById('add-btn') as HTMLAreaElement;
    updateBtn.innerHTML = "Update";

    this.restApiService.getSingleContactData(id).subscribe({
      next: data => {
        const users = JSON.parse(data);
        this.econtent = users.data;
        var img_data = document.getElementById('customer-img') as HTMLImageElement;
        img_data.src = 'assets/images/users/' + this.econtent.image_src
        this.contactsForm.controls['name'].setValue(this.econtent.name);
        this.contactsForm.controls['company'].setValue(this.econtent.company);
        this.contactsForm.controls['designation'].setValue(this.econtent.designation);
        this.contactsForm.controls['email'].setValue(this.econtent.email);
        this.contactsForm.controls['phone'].setValue(this.econtent.phone);
        this.contactsForm.controls['lead_score'].setValue(this.econtent.lead_score);
        this.contactsForm.controls['tags'].setValue(this.econtent.tags);
        this.contactsForm.controls['last_contacted'].setValue(this.econtent.last_contacted);
        this.contactsForm.controls['ids'].setValue(this.econtent._id);
      },
      error: err => {
        this.content = JSON.parse(err.error).message;
      }
    });

  }

  /**
   * View Data Get
   * @param content modal content
   */
  viewDataGet(id: any) {
    this.restApiService.getSingleContactData(id).subscribe({
      next: data => {
        const users = JSON.parse(data);
        this.econtent = users.data;
        var img_data = document.querySelector('.contact-details img') as HTMLImageElement;
        img_data.src = 'assets/images/users/' + this.econtent.image_src;
        (document.querySelector('.contact-details h5') as HTMLImageElement).innerHTML = this.econtent.name;
        (document.querySelector('.contact-details p') as HTMLImageElement).innerHTML = this.econtent.company;
        (document.querySelector('.designation') as HTMLImageElement).innerHTML = this.econtent.designation;
        (document.querySelector('.email') as HTMLImageElement).innerHTML = this.econtent.email;
        (document.querySelector('.phone') as HTMLImageElement).innerHTML = this.econtent.phone;
        (document.querySelector('.l_score') as HTMLImageElement).innerHTML = this.econtent.lead_score;
        (document.querySelector('.tags-list .d-flex') as HTMLImageElement).innerHTML = '';
        this.econtent.tags.forEach((item: any) => {
          (document.querySelector('.tags-list .d-flex') as HTMLImageElement).innerHTML += `<span class="badge bg-primary-subtle text-primary">` + item + `</span>`;
        });
        var date: any = document.querySelector('.contacted_date') as HTMLImageElement;
        date.innerHTML = this.datePipe.transform(new Date(this.econtent.last_contacted), "MMMM d, y");
      },
      error: err => {
        this.content = JSON.parse(err.error).message;
      }
    });
  }

  // The master checkbox will check/ uncheck all items
  checkUncheckAll(ev: any) {
    this.contacts.forEach((x: { state: any; }) => x.state = ev.target.checked)
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.contacts.length; i++) {
      if (this.contacts[i].state == true) {
        result = this.contacts[i];
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";

  }
  isAllChecked() {
    return this.content.every((_: { state: any; }) => _.state);
  }

  /**
  * Multiple Default Select2
  */
  selectValue = ['Lead', 'Partner', 'Exiting', 'Long-term'];

  // Csv File Export
  csvFileExport() {
    var orders = {
      fieldSeparator: ',',
      quoteStrings: '"',
      decimalseparator: '.',
      showLabels: true,
      showTitle: true,
      title: 'Contact Data',
      useBom: true,
      noDownload: false,
      headers: ["Id", "Image src", "Name", "Company", "Designation", "Email", "Phone", "Tags", "Lead Score", "Last Contacted"]
    };
    new ngxCsv(this.content, "Contact", orders);
  }

  // Select Checkbox value Get
  onCheckboxChange(e: any) {
    const checkArray: UntypedFormArray = this.contactsForm.get('subItem') as UntypedFormArray;
    checkArray.push(new UntypedFormControl(e.target.value));
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.contacts.length; i++) {
      if (this.contacts[i].state == true) {
        result = this.contacts[i];
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";
  }

  /**
   * Confirmation mail model
   */
  deleteId: any;
  confirm(content: any, id: any) {
    this.deleteId = id;
    this.modalService.open(content, { centered: true });
  }

  // Delete Data
  deleteData(id: any) {
    if (id) {
      this.restApiService.deleteContact(id).subscribe({
        next: data => { },
        error: err => {
          this.content = JSON.parse(err.error).message;
        }
      });
      document.getElementById('c_' + id)?.remove();
    }
    else {
      this.checkedValGet.forEach((item: any) => {
        document.getElementById('c_' + item)?.remove();
      });
    }
  }

  /**
   * Multiple Delete
   */
  checkedValGet: any[] = [];
  deleteMultiple(content: any) {
    var checkboxes: any = document.getElementsByName('checkAll');
    var result
    var checkedVal: any[] = [];
    for (var i = 0; i < checkboxes.length; i++) {
      if (checkboxes[i].checked) {
        result = checkboxes[i].value;
        checkedVal.push(result);
      }
    }
    if (checkedVal.length > 0) {
      this.modalService.open(content, { centered: true });
    }
    else {
      Swal.fire({ text: 'Please select at least one checkbox', confirmButtonColor: '#299cdb', });
    }
    this.checkedValGet = checkedVal;
  }

  // Sort filter
  sortField: any;
  sortBy: any
  SortFilter() {
    this.sortField = (document.getElementById("choices-single-default") as HTMLInputElement).value;
    if (this.sortField[0] == 'A') {
      this.sortBy = 'desc';
      this.sortField = this.sortField.replace(/A/g, '')
    }
    if (this.sortField[0] == 'D') {
      this.sortBy = 'asc';
      this.sortField = this.sortField.replace(/D/g, '')
    }
  }
  /**
* Sort table data
* @param param0 sort the column
*
*/
  onSort({ column, direction }: contactSortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.contactsortable !== column) {
        header.direction = '';
      }
    });

    this.service.sortColumn = column;
    this.service.sortDirection = direction;
  }




}
