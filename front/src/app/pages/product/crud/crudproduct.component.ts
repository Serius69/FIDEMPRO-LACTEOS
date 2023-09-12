import { Component } from '@angular/core';
import { ProductService } from 'src/app/services/product.service';
import { Product } from 'src/app/core/common/product';

@Component({
  selector: 'app-crudproduct',
  templateUrl: './crudproduct.component.html'
})
export class CrudProductComponent {
  ProductArray: Product[] = [];
  id = 0;
  name = "";
  type = "";
  quantity = 0;
  description = "";

  constructor(private ProductService: ProductService) {
    this.getAll();
  }

  saveRecords() {
    const bodyData = {
      id: this.id, 
      name: this.name,
      type: this.type,
      quantity: this.quantity,
      description: this.description
      
    };

    this.ProductService.create(bodyData).subscribe(resultData => {
      console.log(resultData);
      alert("Product Registered Successfully");
      this.clearForm();
      this.getAll();
    });
  }

  getAll() {
    this.ProductService.getAll().subscribe(resultData => {
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

    this.ProductService.update(this.id.toString(), bodyData).subscribe(resultData => {
      console.log(resultData);
      alert("Product Updated Successfully");
      this.clearForm();
      this.getAll();
    });
  }

  setUpDelete(Product: Product) {
    this.ProductService.delete(Product.id.toString()).subscribe(resultData => {
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
