import { Component, OnInit } from '@angular/core';
import { UsersService } from 'src/app/services/users.service';
import { User } from 'src/app/common/user';
import { ProductService } from 'src/app/services/product.service';
import { Product } from 'src/app/common/product';
// import { Result } from 'src/app/common/result';
import { ResultService } from 'src/app/services/result.service';
import { VariableService } from 'src/app/services/variable.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html'
})
export class ProfileComponent implements OnInit {

  ProductArray: Product[] = [];

  // ResultArray: Result[] = [];
  user: any; // Variable para almacenar los datos del usuario

  constructor(private userService: UsersService, 
              private productService: ProductService,
              // private resultService: ResultService,
              private variableService: VariableService,) {

  }

  ngOnInit(): void {
    // En el método ngOnInit, puedes cargar los datos del usuario desde el servicio
    const userId = 1;
    this.userService.getUser(userId).subscribe((data) => {
      this.user = data; // Asigna los datos del usuario a la variable 'user'
    });
  }
  getAllProduct() {
    this.productService.getAll().subscribe(resultData => {
      console.log(resultData);
      this.ProductArray = resultData;
    });
  }
  // getAllVariable() {
  //   this.variableService.getAll().subscribe(resultData => {
  //     console.log(resultData);
  //     this.ProductArray = resultData;
  //   });
  // }
  // getAllResult() {
  //   this.resultService.getAll().subscribe(resultData => {
  //     console.log(resultData);
  //     this.ProductArray = resultData;
  //   });
  // }

}
