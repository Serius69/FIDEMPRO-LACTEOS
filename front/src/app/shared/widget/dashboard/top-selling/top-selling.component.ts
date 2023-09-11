import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-top-selling',
  templateUrl: './top-selling.component.html',
  styleUrls: ['./top-selling.component.scss']
})
export class TopSellingComponent implements OnInit {

  // Top Selling data
  @Input() TopSelling: Array<{
    image?: string;
    pName?: string;
    subtitle?: string;
    type?: string;
    stock?: string;
    amount?: string;
    percentage?: string;
  }> | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
