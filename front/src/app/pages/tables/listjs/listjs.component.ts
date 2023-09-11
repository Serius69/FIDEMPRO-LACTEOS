import { Component, PipeTransform, QueryList, ViewChildren } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, UntypedFormGroup, FormArray, Validators, FormControl } from '@angular/forms';

// Sweet Alert
import Swal from 'sweetalert2';

import { ListJsModel, paginationModel } from './listjs.model';
import { paginationlist, dataattribute, existingList, FuzzyList } from './data';
import { OrdersService } from './listjs.service';
import { NgbdListSortableHeader, listSortEvent } from './listjs-sortable.directive';

@Component({
  selector: 'app-listjs',
  templateUrl: './listjs.component.html',
  styleUrls: ['./listjs.component.scss'],
  providers: [OrdersService, DecimalPipe]

})

/**
 * Listjs table Component
 */
export class ListjsComponent {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  submitted = false;
  listJsForm!: UntypedFormGroup;
  ListJsData!: ListJsModel[];
  checkedList: any;
  masterSelected!: boolean;
  ListJsDatas: any;

  page: any = 1;
  pageSize: any = 3;
  startIndex: number = 0;
  endIndex: number = 3;
  totalRecords: number = 0;

  paginationDatas: any;
  attributedata: any;
  existingData: any;
  fuzzyData: any;

  existingTerm: any;
  fuzzyTerm: any;
  dataterm: any;
  term: any;

  // Table data
  ListJsList!: Observable<ListJsModel[]>;
  total: Observable<number>;
  @ViewChildren(NgbdListSortableHeader) headers!: QueryList<NgbdListSortableHeader>;

  constructor(private modalService: NgbModal, public service: OrdersService, private formBuilder: UntypedFormBuilder, private pipe: DecimalPipe) {
    this.ListJsList = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Tables' },
      { label: 'Listjs', active: true }
    ];

    /**
     * Form Validation
     */
    this.listJsForm = this.formBuilder.group({
      ids: [''],
      customer_name: ['', [Validators.required]],
      email: ['', [Validators.required]],
      phone: ['', [Validators.required]],
      date: ['', [Validators.required]],
      status: ['', [Validators.required]]
    });


    /**
     * fetches data
     */
    this.ListJsList.subscribe(x => {
      this.ListJsDatas = Object.assign([], x);
    });

    this.attributedata = dataattribute
    this.existingData = existingList
    this.fuzzyData = FuzzyList

    this.paginationDatas = paginationlist
    this.totalRecords = this.paginationDatas.length

    this.startIndex = (this.page - 1) * this.pageSize + 1;
    this.endIndex = (this.page - 1) * this.pageSize + this.pageSize;
    if (this.endIndex > this.totalRecords) {
      this.endIndex = this.totalRecords;
    }
    this.paginationDatas = paginationlist.slice(this.startIndex - 1, this.endIndex);
  }

  /**
 * User grid data fetches
 */
  //  private _fetchData() {
  //   this.ListJsData = ListJs;
  //   this.ListJsDatas = Object.assign([], this.ListJsData);
  // }

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
    return this.listJsForm.controls;
  }

  /**
  * Pagination
  */
  loadPage() {
    this.startIndex = (this.page - 1) * this.pageSize + 1;
    this.endIndex = (this.page - 1) * this.pageSize + this.pageSize;
    if (this.endIndex > this.totalRecords) {
      this.endIndex = this.totalRecords;
    }
    this.paginationDatas = paginationlist.slice(this.startIndex - 1, this.endIndex);
  }


  /**
  * Save saveListJs
  */
  saveListJs() {
    if (this.listJsForm.valid) {
      if (this.listJsForm.get('ids')?.value) {
        this.ListJsDatas = this.ListJsDatas.map((data: { id: any; }) => data.id === this.listJsForm.get('ids')?.value ? { ...data, ...this.listJsForm.value } : data)
      } else {
        const customer_name = this.listJsForm.get('customer_name')?.value;
        const email = this.listJsForm.get('email')?.value;
        const phone = this.listJsForm.get('phone')?.value;
        const date = '14 Apr, 2021';
        const status_color = "success";
        const status = this.listJsForm.get('status')?.value;
        this.ListJsDatas.push({
          customer_name,
          email,
          phone,
          date,
          status_color,
          status
        });
        this.modalService.dismissAll()
      }
    }
    this.modalService.dismissAll();
    setTimeout(() => {
      this.listJsForm.reset();
    }, 2000);
    this.submitted = true
  }

  // The master checkbox will check/ uncheck all items
  checkUncheckAll(ev: any) {
    this.ListJsDatas.forEach((x: { state: any; }) => x.state = ev.target.checked)
  }

  /**
  * Confirmation mail model
  */
  deleteId: any;
  confirm(content: any, id: any) {
    this.deleteId = id;
    this.modalService.open(content, { centered: true });
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

  // Delete Data
  deleteData(id: any) {
    if (id) {
      document.getElementById('lj_' + id)?.remove();
    }
    else {
      this.checkedValGet.forEach((item: any) => {
        document.getElementById('lj_' + item)?.remove();
      });
    }
  }

  /**
  * Open modal
  * @param content modal content
  */
  editModal(content: any, id: any) {
    this.submitted = false;
    this.modalService.open(content, { size: 'md', centered: true });
    var updateBtn = document.getElementById('add-btn') as HTMLAreaElement;
    updateBtn.innerHTML = "Update";
    var listData = this.ListJsDatas.filter((data: { id: any; }) => data.id === id);
    this.listJsForm.controls['customer_name'].setValue(listData[0].customer_name);
    this.listJsForm.controls['email'].setValue(listData[0].email);
    this.listJsForm.controls['phone'].setValue(listData[0].phone);
    this.listJsForm.controls['date'].setValue(listData[0].date);
    this.listJsForm.controls['status'].setValue(listData[0].status);
    this.listJsForm.controls['ids'].setValue(listData[0].id);
  }
  /**
  * Sort table data
  * @param param0 sort the column
  *
  */
  onSort({ column, direction }: listSortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.listsortable !== column) {
        header.direction = '';
      }
    });

    this.service.sortColumn = column;
    this.service.sortDirection = direction;
  }


}
