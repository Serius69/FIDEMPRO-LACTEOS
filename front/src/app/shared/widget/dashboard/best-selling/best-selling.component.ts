import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-best-selling',
  templateUrl: './best-selling.component.html',
  styleUrls: ['./best-selling.component.scss']
})
export class BestSellingComponent implements OnInit {

  // Best Selling data
  @Input() BestSelling: Array<{
    image?: string;
    pName?: string;
    date?: string;
    price?: string;
    orders?: string;
    stock?: string;
    amount?: string;
  }> | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
