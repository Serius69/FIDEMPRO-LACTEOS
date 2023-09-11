import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-recent-orders',
  templateUrl: './recent-orders.component.html',
  styleUrls: ['./recent-orders.component.scss']
})
export class RecentOrdersComponent implements OnInit {

   // Recent Orders data
   @Input() Recentelling: Array<{
    id?: string;
    image?: string;
    customer?: string;
    product?: string;
    amount?: string;
    vendor?: string;
    status?: string;
    rating?: string;
    average?: string;
  }> | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
