import { Component, QueryList, ViewChildren } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, UntypedFormGroup, FormArray, Validators } from '@angular/forms';

// Rest Api Service
import { restApiService } from "../../../core/services/rest-api.service";

// Csv File Export
import { ngxCsv } from 'ngx-csv/ngx-csv';

// Sweet Alert
import Swal from 'sweetalert2';

import { CompaniesModel } from './companies.model';
import { Companies } from './data';
import { CompaniesService } from './companies.service';
import { NgbdCompaniesSortableHeader, companySortEvent } from './companies-sortable.directive';

@Component({
  selector: 'app-companies',
  templateUrl: './companies.component.html',
  styleUrls: ['./companies.component.scss'],
  providers: [CompaniesService, DecimalPipe]
})

/**
 * Companies Component
 */
export class CompaniesComponent {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  submitted = false;
  companiesForm!: UntypedFormGroup;
  CustomersData!: CompaniesModel[];
  masterSelected!: boolean;
  checkedList: any;

  // Api Data
  content?: any;
  company?: any;
  econtent?: any;

  // Table data
  // Table data
  CompaniesList!: Observable<CompaniesModel[]>;
  total: Observable<number>;
  @ViewChildren(NgbdCompaniesSortableHeader) headers!: QueryList<NgbdCompaniesSortableHeader>;

  constructor(private modalService: NgbModal, public service: CompaniesService, private formBuilder: UntypedFormBuilder, private restApiService: restApiService) {
    this.CompaniesList = service.company$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'CRM' },
      { label: 'Companies', active: true }
    ];

    /**
     * Form Validation
     */
    this.companiesForm = this.formBuilder.group({
      ids: [''],
      image_src: ['brands/dribbble.png'],
      name: ['', [Validators.required]],
      owner: ['', [Validators.required]],
      industry_type: ['', [Validators.required]],
      star_value: ['', [Validators.required]],
      location: ['', [Validators.required]],
      employee: ['', [Validators.required]],
      website: ['', [Validators.required]],
      contact_email: ['', [Validators.required]],
      since: ['', [Validators.required]]
    });

    /**
     * fetches data
     */
    setTimeout(() => {
      this.CompaniesList.subscribe(x => {
        this.content = this.company;
        this.company = Object.assign([], x);
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
    this.modalService.open(content, { size: 'lg', centered: true });
  }

  /**
   * Form data get
   */
  get form() {
    return this.companiesForm.controls;
  }

  // File Upload
  imageURL: string | undefined;
  fileChange(event: any) {
    let fileList: any = (event.target as HTMLInputElement);
    let file: File = fileList.files[0];
    document.getElementById('')
    this.companiesForm.patchValue({
      // image_src: file.name
      image_src: 'brands/dribbble.png'
    });
    const reader = new FileReader();
    reader.onload = () => {
      this.imageURL = reader.result as string;
      (document.getElementById('companylogo-img') as HTMLImageElement).src = this.imageURL;
    }
    reader.readAsDataURL(file)
  }

  /**
  * Save user
  */
  saveUser() {
    if (this.companiesForm.valid) {
      if (this.companiesForm.get('ids')?.value) {
        this.restApiService.patchCompanyData(this.companiesForm.value).subscribe(
          (data: any) => {
            this.service.company = this.content.map((order: { _id: any; }) => order._id === data.data.ids ? { ...order, ...data.data } : order);
            this.modalService.dismissAll();
          }
        )
      }
      else {
        this.restApiService.postCompanyData(this.companiesForm.value).subscribe(
          (data: any) => {
            this.service.company.push(data.data);
            this.modalService.dismissAll();
            let timerInterval: any;
            Swal.fire({
              title: 'Company inserted successfully!',
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
      this.companiesForm.reset();
    }, 2000);
    this.submitted = true
  }

  /**
   * View Data Get
   * @param content modal content
   */
  viewDataGet(id: any) {
    this.restApiService.getSingleCompanyData(id).subscribe({
      next: data => {
        const users = JSON.parse(data);
        this.econtent = users.data;

        var img_data = document.querySelector('.company-details img') as HTMLImageElement;
        img_data.src = 'assets/images/' + this.econtent.image_src;
        (document.querySelector('.company-details h5') as HTMLImageElement).innerHTML = this.econtent.name;
        (document.querySelector('.company-details p') as HTMLImageElement).innerHTML = this.econtent.owner;
        (document.querySelector('.industry_type') as HTMLImageElement).innerHTML = this.econtent.industry_type;
        (document.querySelector('.location') as HTMLImageElement).innerHTML = this.econtent.location;
        (document.querySelector('.employee') as HTMLImageElement).innerHTML = this.econtent.employee;
        (document.querySelector('.rating') as HTMLImageElement).innerHTML = this.econtent.star_value;
        (document.querySelector('.website') as HTMLImageElement).innerHTML = this.econtent.website;
        (document.querySelector('.email') as HTMLImageElement).innerHTML = this.econtent.contact_email;
        (document.querySelector('.since') as HTMLImageElement).innerHTML = this.econtent.since;
      },
      error: err => {
        this.content = JSON.parse(err.error).message;
      }
    });
  }

  /**
   * Open Edit modal
   * @param content modal content
   */
  editDataGet(id: any, content: any) {
    this.submitted = false;
    this.modalService.open(content, { size: 'lg', centered: true });
    var modelTitle = document.querySelector('.modal-title') as HTMLAreaElement;
    // modelTitle.innerHTML = 'Edit Company';
    var updateBtn = document.getElementById('add-btn') as HTMLAreaElement;
    updateBtn.innerHTML = "Update";

    this.restApiService.getSingleCompanyData(id).subscribe({
      next: data => {
        const users = JSON.parse(data);
        this.econtent = users.data;
        var img_data = document.getElementById('companylogo-img') as HTMLImageElement;
        img_data.src = 'assets/images/' + this.econtent.image_src
        this.companiesForm.controls['name'].setValue(this.econtent.name);
        this.companiesForm.controls['owner'].setValue(this.econtent.owner);
        this.companiesForm.controls['industry_type'].setValue(this.econtent.industry_type);
        this.companiesForm.controls['star_value'].setValue(this.econtent.star_value);
        this.companiesForm.controls['location'].setValue(this.econtent.location);
        this.companiesForm.controls['employee'].setValue(this.econtent.employee);
        this.companiesForm.controls['website'].setValue(this.econtent.website);
        this.companiesForm.controls['contact_email'].setValue(this.econtent.contact_email);
        this.companiesForm.controls['since'].setValue(this.econtent.since);
        this.companiesForm.controls['ids'].setValue(this.econtent._id);
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
      this.restApiService.deleteCompany(id).subscribe({
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

  // The master checkbox will check/ uncheck all items
  checkUncheckAll(ev: any) {
    this.company.forEach((x: { state: any; }) => x.state = ev.target.checked)
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < this.company.length; i++) {
      if (this.company[i].state == true) {
        result = this.company[i];
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
    for (var i = 0; i < this.company.length; i++) {
      if (this.company[i].state == true) {
        result = this.company[i];
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    checkedVal.length > 0 ? (document.getElementById("remove-actions") as HTMLElement).style.display = "block" : (document.getElementById("remove-actions") as HTMLElement).style.display = "none";
  }

  // Csv File Export
  csvFileExport() {
    var orders = {
      fieldSeparator: ',',
      quoteStrings: '"',
      decimalseparator: '.',
      showLabels: true,
      showTitle: true,
      title: 'Company Data',
      useBom: true,
      noDownload: false,
      headers: ["Id", "Name", "Owner", "Industry Type", "Star Value", "Location", "Employee", "Website", "Contact Email", "Since", "Image src"]
    };
    new ngxCsv(this.content, "Company", orders);
  }

  // Sort filter
  sortField: any;
  sortBy: any
  SortFilter() {
    this.sortField = (document.getElementById("choices-single-default") as HTMLInputElement).value;
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
  onSort({ column, direction }: companySortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.companiesortable !== column) {
        header.direction = '';
      }
    });

    this.service.sortColumn = column;
    this.service.sortDirection = direction;
  }

}
