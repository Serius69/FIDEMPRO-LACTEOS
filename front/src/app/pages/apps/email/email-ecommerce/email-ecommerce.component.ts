import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-email-ecommerce',
  templateUrl: './email-ecommerce.component.html',
  styleUrls: ['./email-ecommerce.component.scss']
})

/**
 * Email Ecommerce Component
 */
export class EmailEcommerceComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  constructor() { }

  ngOnInit(): void {
    /**
     * BreadCrumb
     */
     this.breadCrumbItems = [
      { label: 'Email' },
      { label: 'Ecommerce Action', active: true }
    ];
  }

  // Click Scroll Top
  inView(ele:any){
    ele.scrollIntoView({behavior:"smooth", block:"start", inline:"start"})
  }

}
