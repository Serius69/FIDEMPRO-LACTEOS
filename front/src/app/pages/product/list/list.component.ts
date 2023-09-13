import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ProductService } from 'src/app/pages/product/product.service';
import { Product } from 'src/app/core/common/product';

import { projectListWidgets, projectListWidgets1, projectListWidgets2 } from './data';
import { projectListModel, projectListModel1, projectListModel2 } from './list.model';
import { listService } from './list.service';
import { DecimalPipe } from '@angular/common';
@Component({
  selector: 'app-list',
  templateUrl: './list.component.html',
  providers: [listService, DecimalPipe]
})
export class ListComponent implements OnInit {
  ProductArray: Product[] = [];
  id = 0;
  name = "";
  type = "";
  quantity = 0;
  description = "";

// bread crumb items
  breadCrumbItems!: Array<{}>;
  projectListWidgets!: projectListModel[];
  projectListWidgets1!: projectListModel1[];
  projectListWidgets2!: projectListModel2[];
  projectmodel!: Observable<projectListModel2[]>;
  total: Observable<number>;
  sellers?: any;
  ProductService: any;

  constructor(private modalService: NgbModal,
    public service: listService) {
    this.projectmodel = service.companies$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Projects' },
      { label: 'Project List', active: true }
    ];

    /**
     * Fetches the data
     */
    this.fetchData();
  }

  /**
   * Fetches the data
   */
  private fetchData() {
    // this.projectListWidgets = projectListWidgets;
    this.projectListWidgets1 = projectListWidgets1;
    this.projectListWidgets2 = projectListWidgets2;
    setTimeout(() => {
      this.projectmodel.subscribe(x => {
        this.projectListWidgets = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1200);
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
    document.getElementById('pl1_' + id)?.remove();
  }

  /**
   * Active Toggle navbar
   */
  activeMenu(id: any) {
    document.querySelector('.heart_icon_' + id)?.classList.toggle('active');
  }


  saveRecords() {
    const bodyData = {
      id: this.id, 
      name: this.name,
      type: this.type,
      quantity: this.quantity,
      description: this.description
      
    };

    this.ProductService.create(bodyData).subscribe((resultData: any) => {
      console.log(resultData);
      alert("Product Registered Successfully");
      this.clearForm();
      this.getAll();
    });
  }

  getAll() {
    this.ProductService.getAll().subscribe((resultData: any) => {
      console.log(resultData);
      this.ProductArray = resultData;
    });
  }

  setUpUpdate(Product: Product) {
    this.id = Product.id;
    this.name = Product.name;
    this.type = Product.type;
    this.description = Product.description;
  }

  updateRecords() {
    const bodyData = {
      id: this.id,
      name: this.name,
      type: this.type,
      quantity: this.quantity,
      description: this.description
    };

    this.ProductService.update(this.id.toString(), bodyData).subscribe((resultData: any) => {
      console.log(resultData);
      alert("Product Updated Successfully");
      this.clearForm();
      this.getAll();
    });
  }

  setUpDelete(Product: Product) {
    this.ProductService.delete(Product.id.toString()).subscribe((resultData: any) => {
      console.log(resultData);
      alert("Product Deleted Successfully");
      this.getAll();
    });
  }

  clearForm() {
    this.id = 0;
    this.name = "";
    this.type = "";
    this.quantity = 0;
    this.description = "";
  }
}
