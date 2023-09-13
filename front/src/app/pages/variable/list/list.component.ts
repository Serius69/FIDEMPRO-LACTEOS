import { Component, QueryList, ViewChildren } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { NgbModal, NgbNavChangeEvent } from '@ng-bootstrap/ng-bootstrap';
import { UntypedFormBuilder, UntypedFormGroup, FormArray, FormControl, Validators } from '@angular/forms';
// Range Slider
import { Options } from '@angular-slider/ngx-slider';

// Sweet Alert
import Swal from 'sweetalert2';

import { Variable } from 'src/app/core/common/variable';
import { AdvancedService } from '../../variable/variable.service';
import { NgbdProductsSortableHeader, productSortEvent } from '../variable-sortable.directive';

// Products Services
import { restApiService } from "../../../core/services/rest-api.service";
import { GlobalComponent } from '../../../global-component';
import { Router } from '@angular/router';

@Component({
  selector: 'app-list',
  templateUrl: './list.component.html',
  providers: [AdvancedService, DecimalPipe]
})

/**
 * Products Components
 */
export class ListComponent {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  url = GlobalComponent.API_URL;
  content!: Variable[];
  products!: any;
  user = [];
  Brand: any = [];
  Rating: any = [];
  discountRates: number[] = [];
  contactsForm!: UntypedFormGroup;
  total: any;
  totalbrand: any;
  totalrate: any;
  totaldiscount: any;
  allproduct: any;

  allproducts: any;
  activeindex = '1';
  allpublish: any;
  grocery: any = 0;
  fashion: any = 0;
  watches: any = 0;
  electronics: any = 0;
  furniture: any = 0;
  accessories: any = 0;
  appliance: any = 0;
  kids: any = 0;
  totalpublish: any = 0;

  // Table data
  productList!: Observable<Variable[]>;
  allproductList!: Observable<Variable[]>;
  total$: Observable<number>;
  @ViewChildren(NgbdProductsSortableHeader) headers!: QueryList<NgbdProductsSortableHeader>;
  searchproducts: any;
  publishedproduct: any;


  constructor(private modalService: NgbModal,
    private router: Router,
    public service: AdvancedService,
    private formBuilder: UntypedFormBuilder,
    public restApiService: restApiService) {
    this.productList = service.countries$;
    this.total$ = service.total$;
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Ecommerce' },
      { label: 'Products', active: true }
    ];


    /**
     * fetches data
     */
    setTimeout(() => {
      this.productList.subscribe(x => {
        this.content = this.products;
        this.products = Object.assign([], x);
      });

      this.allproductList.subscribe(x => {
        this.allproducts = Object.assign([], x);
      });
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1000)

    setTimeout(() => {
      for (var i = 0; i < this.allproducts.length; i++) {
        if (this.allproducts[i].category == 'Kitchen Storage & Containers') {
          this.grocery += 1
        }
        if (this.allproducts[i].category == 'Clothes') {
          this.fashion += 1
        }
        if (this.allproducts[i].category == 'Watches') {
          this.watches += 1
        } if (this.allproducts[i].category == 'Electronics') {
          this.electronics += 1
        } if (this.allproducts[i].category == 'Furniture') {
          this.furniture += 1
        } if (this.allproducts[i].category == 'Bike Accessories') {
          this.accessories += 1
        }
        if (this.allproducts[i].category == 'Tableware & Dinnerware') {
          this.appliance += 1
        }
        if (this.allproducts[i].category == 'Bags, Wallets and Luggage') {
          this.kids += 1
        }
        if (this.allproducts[i].status == 'published') {
          this.totalpublish += 1
        }
      }
    }, 2000);

    /**
   * Form Validation
   */
    this.contactsForm = this.formBuilder.group({
      subItem: this.formBuilder.array([]),
    });
  }

  /**
   * Pagination
   */
  // loadPage(page: number) {
  //   this.startIndex = (this.page - 1) * this.pageSize + 1;
  //   this.endIndex = (this.page - 1) * this.pageSize + this.pageSize;
  //   if (this.endIndex > this.totalRecords) {
  //     this.endIndex = this.totalRecords;
  //   }
  //   this.products = this.allproducts.slice(this.startIndex - 1, this.endIndex);
  // }

  /**
  * Sort table data
  * @param param0 sort the column
  *
  */
  onSort({ column, direction }: productSortEvent) {
    // resetting other headers
    this.headers.forEach(header => {
      if (header.productsortable !== column) {
        header.direction = '';
      }
    });

    this.service.sortColumn = column;
    this.service.sortDirection = direction;
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
      this.restApiService.deleteData(id).subscribe({
        next: data => { },
        error: err => {
          this.content = JSON.parse(err.error).message;
        }
      });
      document.getElementById('p_' + id)?.remove();
    }
    else {
      this.checkedValGet.forEach((item: any) => {
        document.getElementById('p_' + item)?.remove();
      });
      (document.getElementById("selection-element") as HTMLElement).style.display = "none"
    }
  }

  // Price Slider
  minValue = 0;
  maxValue = 1000;
  options: Options = {
    floor: 0,
    ceil: 1000
  };

  /**
   * Default Select2
   */
  multiDefaultOption = 'Watches';
  selectedAccount = 'This is a placeholder';
  Default = [
    { name: 'Watches' },
    { name: 'Headset' },
    { name: 'Sweatshirt' },
  ];

  // Check Box Checked Value Get
  checkedValGet: any[] = [];
  // Select Checkbox value Get
  onCheckboxChange(e: any) {
    var checkboxes: any = document.getElementsByName('checkAll');
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < checkboxes.length; i++) {
      if (checkboxes[i].checked) {
        result = checkboxes[i].value;
        checkedVal.push(result);
      }
    }
    this.checkedValGet = checkedVal
    var checkBoxCount: any = document.getElementById('select-content') as HTMLElement;
    checkBoxCount.innerHTML = checkedVal.length;
    checkedVal.length > 0 ? (document.getElementById("selection-element") as HTMLElement).style.display = "block" : (document.getElementById("selection-element") as HTMLElement).style.display = "none";
  }
  /**
    * Brand Filter
    */
  changeBrand(e: any) {
    if (e.target.checked) {
      this.Brand.push(e.target.defaultValue)
    } else {
      for (var i = 0; i < this.Brand.length; i++) {
        if (this.Brand[i] === e.target.defaultValue) {
          this.Brand.splice(i, 1)
        }
      }
    }
    this.totalbrand = this.Brand.length
  }

  /**
  * Discount Filter
  */
  changeDiscount(e: any) {
    if (e.target.checked) {
      this.discountRates.push(e.target.defaultValue)

      this.productList.subscribe(x => {
        this.products = x.filter((product: any) => {
          return product.rating > e.target.defaultValue;
        });
      });
    } else {
      for (var i = 0; i < this.discountRates.length; i++) {
        if (this.discountRates[i] === e.target.defaultValue) {
          this.discountRates.splice(i, 1)
        }
      }
    }
    this.totaldiscount = this.discountRates.length
  }

  /**
   * Product Filtering  
   */
  changeProducts(e: any, name: any, category: any) {
    const iconItems = document.querySelectorAll('.filter-list');
    iconItems.forEach((item: any) => {
      var el = item.querySelectorAll('a')
      el.forEach((item: any) => {
        var element = item.querySelector('h5').innerHTML
        if (element == category) {
          item.classList.add("active");
        } else {
          item.classList.remove("active");
        }
      })
    });

    this.service.ProductFilter = name
  }


  /**
  * Search Product
  */
  search(value: string) {
    if (this.activeindex == '1') {
      if (value) {
        this.products = this.allproducts.filter((val: any) =>
          val.category.toLowerCase().includes(value)
        );
        this.total = this.products.length;
      } else {
        this.products = this.searchproducts
        this.total = this.allproducts.length;
      }
    } else if (this.activeindex == '2') {
      if (value) {
        this.publishedproduct = this.publishedproduct.filter((val: any) =>
          val.category.toLowerCase().includes(value)
        );
        this.total = this.publishedproduct.length;
      } else {
        this.publishedproduct = this.allpublish
        this.total = this.publishedproduct.length;
      }
    }

  }

  /**
  * Range Slider Wise Data Filter
  */
  valueChange(value: number, boundary: boolean): void {
    if (value > 0 && value < 1000) {
      if (this.activeindex == '1') {
        if (boundary) {
          this.minValue = value;
        } else {
          this.maxValue = value;
        }
      } else if (this.activeindex == '2') {
        if (boundary) {
          this.minValue = value;
        } else {
          this.maxValue = value;
        }
      }
    }
  }

  clearall(ev: any) {
    this.minValue = 0;
    this.maxValue = 1000;
    var checkboxes: any = document.getElementsByName('checkAll');
    for (var i = 0; i < checkboxes.length; i++) {
      checkboxes[i].checked = false
    }
    // this.service.searchTerm = ''
    this.totalbrand = 0;
    this.totaldiscount = 0;
    this.totalrate = 0;
    this.Brand = []
    this.Rating = []
    this.discountRates = []
    const iconItems = document.querySelectorAll('.filter-list');
    iconItems.forEach((item: any) => {
      var el = item.querySelectorAll('a')
      el.forEach((item: any) => {
        item.classList.remove("active");
      })
    });
    this.service.searchTerm = '';
    this.service.ProductFilter = '';
  }

  godetail(id: any) {
    this.router.navigate(['/ecommerce/product-detail/1', this.products[id]])
  }

  gopublishdetail(id: any) {
    // this.router.navigate(['/ecommerce/product-detail/1', this.publishedproduct[id]])
  }

}
