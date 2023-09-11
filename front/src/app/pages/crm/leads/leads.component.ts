import { Component, QueryList, ViewChildren, TemplateRef } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { NgbModal, NgbOffcanvas } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, UntypedFormGroup, FormArray, Validators } from '@angular/forms';

// Date Format
import { DatePipe } from '@angular/common';

import { restApiService } from "../../../core/services/rest-api.service";

// Sweet Alert
import Swal from 'sweetalert2';

import { LeadsModel } from './leads.model';
import { Leads } from './data';
import { LeadsService } from './leads.service';
import { NgbdLeadsSortableHeader, leadSortEvent } from './leads-sortable.directive';

@Component({
  selector: 'app-leads',
  templateUrl: './leads.component.html',
  styleUrls: ['./leads.component.scss'],
  providers: [LeadsService, DecimalPipe]
})
/**
 * Leads Component
 */
export class LeadsComponent {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  submitted = false;
  leadsForm!: UntypedFormGroup;
  CustomersData!: LeadsModel[];
  masterSelected!: boolean;
  checkedList: any;

  // Api Data
  content?: any;
  leads?: any;
  econtent?: any;

  // Table data
  invoiceList!: Observable<LeadsModel[]>;
  total: Observable<number>;
  @ViewChildren(NgbdLeadsSortableHeader) headers!: QueryList<NgbdLeadsSortableHeader>;
  closeResult: any;

  constructor(private modalService: NgbModal, public service: LeadsService, private formBuilder: UntypedFormBuilder, private restApiService: restApiService, private offcanvasService: NgbOffcanvas, private datePipe: DatePipe) {
    this.invoiceList = service.leads$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'CRM' },
      { label: 'Leads', active: true }
    ];

    /**
     * Form Validation
     */
    this.leadsForm = this.formBuilder.group({
      image_src: ['avatar-8.jpg'],
      ids: [''],
      name: ['', [Validators.required]],
      company: ['', [Validators.required]],
      score: ['', [Validators.required]],
      phone: ['', [Validators.required]],
      location: ['', [Validators.required]],
      tags: ['', [Validators.required]],
      date: ['', [Validators.required]]
    });

    /**
     * fetches data
     */
    setTimeout(() => {
      this.invoiceList.subscribe(x => {
        this.content = this.leads;
        this.leads = Object.assign([], x);
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
    return this.leadsForm.controls;
  }

  // File Upload
  imageURL: string | undefined;
  fileChange(event: any) {
    let fileList: any = (event.target as HTMLInputElement);
    let file: File = fileList.files[0];
    document.getElementById('')
    this.leadsForm.patchValue({
      // image_src: file.name
      image_src: 'avatar-8.jpg'
    });
    const reader = new FileReader();
    reader.onload = () => {
      this.imageURL = reader.result as string;
      (document.getElementById('lead-img') as HTMLImageElement).src = this.imageURL;
    }
    reader.readAsDataURL(file)
  }

  /**
  * Save user
  */
  saveUser() {
    if (this.leadsForm.valid) {
      if (this.leadsForm.get('ids')?.value) {
        this.restApiService.patchLeadData(this.leadsForm.value).subscribe(
          (data: any) => {
            this.service.leads = this.content.map((order: { _id: any; }) => order._id === data.data.ids ? { ...order, ...data.data } : order);
            this.modalService.dismissAll();
          }
        )
      }
      else {
        this.restApiService.postContactData(this.leadsForm.value).subscribe(
          (data: any) => {
            this.service.leads.push(data.data);
            this.modalService.dismissAll();
            let timerInterval: any;
            Swal.fire({
              title: 'Leads inserted successfully!',
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
      this.leadsForm.reset();
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
    modelTitle.innerHTML = 'Edit Lead';
    var updateBtn = document.getElementById('add-btn') as HTMLAreaElement;
    updateBtn.innerHTML = "Update";

    this.restApiService.getSingLeadData(id).subscribe({
      next: data => {
        const users = JSON.parse(data);
        this.econtent = users.data;
        var img_data = document.getElementById('lead-img') as HTMLImageElement;
        img_data.src = 'assets/images/users/' + this.econtent.image_src
        this.leadsForm.controls['name'].setValue(this.econtent.name);
        this.leadsForm.controls['company'].setValue(this.econtent.company);
        this.leadsForm.controls['score'].setValue(this.econtent.score);
        this.leadsForm.controls['phone'].setValue(this.econtent.phone);
        this.leadsForm.controls['location'].setValue(this.econtent.location);
        this.leadsForm.controls['tags'].setValue(this.econtent.tags);
        this.leadsForm.controls['date'].setValue(this.econtent.date);
        this.leadsForm.controls['ids'].setValue(this.econtent._id);
      },
      error: err => {
        this.content = JSON.parse(err.error).message;
      }
    });

  }

  /**
   * Delete model
   */
  deleteId: any;
  confirm(content: any, id: any) {
    this.deleteId = id;
    this.modalService.open(content, { centered: true });
  }

  // Delete Data
  deleteData(id: any) {
    if (id) {
      this.restApiService.deletelead(id).subscribe({
        next: data => { },
        error: err => {
          this.content = JSON.parse(err.error).message;
        }
      });
      document.getElementById('l_' + id)?.remove();
    }
    else {
      this.checkedValGet.forEach((item: any) => {
        document.getElementById('l_' + item)?.remove();
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

  // The master checkbox will check/ uncheck all items
  checkUncheckAll(ev: any) {
    this.leads.forEach((x: { state: any; }) => x.state = ev.target.checked)
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.leads.length; i++) {
      if (this.leads[i].state == true) {
        result = this.leads[i];
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";

  }

  // Select Checkbox value Get
  onCheckboxChange(e: any) {
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.leads.length; i++) {
      if (this.leads[i].state == true) {
        result = this.leads[i];
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";
  }

  /**
  * Multiple Default Select2
  */
  selectValue = ['Lead', 'Partner', 'Exiting', 'Long-term'];

  //  Filter Offcanvas Set
  openEnd(content: TemplateRef<any>) {
    this.offcanvasService.open(content, { position: 'end' });
  }

  // Filtering
  isstatus?: any
  SearchData() {
    var date = document.getElementById("isDate") as HTMLInputElement;
    var dateVal = date.value ? this.datePipe.transform(new Date(date.value), "yyyy-MM-dd") : '';

    if (dateVal != '') {
      this.leads = this.content.filter((order: any) => {
        return this.datePipe.transform(new Date(order.date), "yyyy-MM-dd") == dateVal;
      });
    }
    else {
      this.leads = this.content;
    }
  }
  /**
* Sort table data
* @param param0 sort the column
*
*/
onSort({ column, direction }: leadSortEvent) {
  // resetting other headers
  this.headers.forEach(header => {
    if (header.leadsortable !== column) {
      header.direction = '';
    }
  });

  this.service.sortColumn = column;
  this.service.sortDirection = direction;
}
}
