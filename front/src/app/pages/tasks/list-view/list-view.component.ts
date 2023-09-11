import { Component, QueryList, ViewChildren } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, UntypedFormGroup, UntypedFormArray, UntypedFormControl, Validators } from '@angular/forms';

// Sweet Alert
import Swal from 'sweetalert2';

// Date Format
import { DatePipe } from '@angular/common';

import { Country, Assigned } from './list-view.model';
import { COUNTRIES, AssignedData } from './data';
import { ListViewService } from './list-view.service';
import { NgbdListViewSortableHeader, SortEvent } from './list-view-sortable.directive';

// Rest Api Service
import { restApiService } from "../../../core/services/rest-api.service";
import { GlobalComponent } from '../../../global-component';

@Component({
  selector: 'app-list-view',
  templateUrl: './list-view.component.html',
  styleUrls: ['./list-view.component.scss'],
  providers: [ListViewService, DecimalPipe]
})

/**
 * ListView Component
 */
export class ListViewComponent {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  submitted = false;
  tasksForm!: UntypedFormGroup;
  CustomersData!: Country[];
  AssignedData!: Assigned[];
  checkedList: any;
  masterSelected!: boolean;

  url = GlobalComponent.API_URL;
  content?: any;
  tasks?: any;
  econtent?: any;

  // Table data
  listViewList!: Observable<Country[]>;
  total: Observable<number>;
  @ViewChildren(NgbdListViewSortableHeader) headers!: QueryList<NgbdListViewSortableHeader>;

  constructor(private modalService: NgbModal, public service: ListViewService, private formBuilder: UntypedFormBuilder, private restApiService: restApiService, private datePipe: DatePipe) {
    this.listViewList = service.customers$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Tasks' },
      { label: 'Tasks List', active: true }
    ];

    /**
     * Form Validation
     */
    this.tasksForm = this.formBuilder.group({
      taskId: "#VLZ1",
      ids: [''],
      project: ['', [Validators.required]],
      task: ['', [Validators.required]],
      creater: ['', [Validators.required]],
      subItem: this.formBuilder.array([]),
      dueDate: ['', [Validators.required]],
      status: ['', [Validators.required]],
      priority: ['', [Validators.required]]
    });

    /**
     * fetches data
     */
    setTimeout(() => {
      this.AssignedData = AssignedData;
      this.listViewList.subscribe(x => {
        this.content = this.tasks;
        this.tasks = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200);

  }

  /**
  * Sort table data
  * @param param0 sort the column
  *
  */
  onSort({ column, direction }: SortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.sortable !== column) {
        header.direction = '';
      }
    });

    this.service.sortColumn = column;
    this.service.sortDirection = direction;
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
    return this.tasksForm.controls;
  }

  /**
  * Save user
  */
  saveUser() {
    if (this.tasksForm.valid) {
      if (this.tasksForm.get('ids')?.value) {
        this.restApiService.patchOrderData(this.tasksForm.value).subscribe(
          (data: any) => {
            this.service.customers = this.content.map((order: { _id: any; }) => order._id === data.data.ids ? { ...order, ...data.data } : order);
         this.modalService.dismissAll();
          }
        )
      }
      else {
        this.restApiService.postTaskData(this.tasksForm.value).subscribe(
          (data: any) => {
            this.service.customers.push(data.data);
            this.modalService.dismissAll();
            let timerInterval: any;
            Swal.fire({
              title: 'Task inserted successfully!',
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
      this.tasksForm.reset();
    }, 2000);
    this.submitted = true
  }

  onCheckboxChange(e: any) {
    const checkArray: UntypedFormArray = this.tasksForm.get('subItem') as UntypedFormArray;
    checkArray.push(new UntypedFormControl(e.target.value));
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.tasks.length; i++) {
      if (this.tasks[i].state == true) {
        result = this.tasks[i];
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";

  }

  /**
   * Open Edit modal
   * @param content modal content
   */
  editDataGet(id: any, content: any) {
    this.submitted = false;
    this.modalService.open(content, { size: 'md', centered: true });
    var modelTitle = document.querySelector('.modal-title') as HTMLAreaElement;
    modelTitle.innerHTML = 'Edit Task';
    var updateBtn = document.getElementById('add-btn') as HTMLAreaElement;
    updateBtn.innerHTML = "Update";

    this.restApiService.getSingleTaskData(id).subscribe({
      next: data => {
        const users = JSON.parse(data);
        this.econtent = users.data;
        this.tasksForm.controls['project'].setValue(this.econtent.project);
        this.tasksForm.controls['task'].setValue(this.econtent.task);
        this.tasksForm.controls['creater'].setValue(this.econtent.creater);
        this.tasksForm.controls['dueDate'].setValue(this.econtent.dueDate);
        this.tasksForm.controls['status'].setValue(this.econtent.status);
        this.tasksForm.controls['priority'].setValue(this.econtent.priority);
        this.tasksForm.controls['ids'].setValue(this.econtent._id);
      },
      error: err => {
        this.content = JSON.parse(err.error).message;
      }
    });
  }

  /**
   * Delete Swal data
   */
  deleteId: any;
  confirm(content: any, id: any) {
    this.deleteId = id;
    this.modalService.open(content, { centered: true });
  }

  // Delete Data
  deleteData(id: any) {
    if (id) {
      this.restApiService.deleteTask(id).subscribe({
        next: data => { },
        error: err => {
          this.content = JSON.parse(err.error).message;
        }
      });
      document.getElementById('t_' + id)?.remove();
    }
    else {
      this.checkedValGet.forEach((item: any) => {
        document.getElementById('t_' + item)?.remove();
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
    this.tasks.forEach((x: { state: any; }) => x.state = ev.target.checked)
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.tasks.length; i++) {
      if (this.tasks[i].state == true) {
        result = this.tasks[i];
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";
  }

  // Filtering
  isstatus?: any
  SearchData() {
    var status = document.getElementById("idStatus") as HTMLInputElement;
    var payment = document.getElementById("idPayment") as HTMLInputElement;
    var date = document.getElementById("isDate") as HTMLInputElement;
    var dateVal = date.value ? this.datePipe.transform(new Date(date.value), "yyyy-MM-dd") : '';
    if (status.value != 'all' && status.value != '' || dateVal != '') {
      this.tasks = this.content.filter((task: any) => {
        return task.status === status.value || this.datePipe.transform(new Date(task.dueDate), "yyyy-MM-dd") == dateVal;
      });
    }
    else {
      this.tasks = this.content;
    }
  }

}
