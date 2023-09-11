import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-crypto-stat',
  templateUrl: './crypto-stat.component.html',
  styleUrls: ['./crypto-stat.component.scss']
})

/**
 * Crypto Stat Component 
 */
export class CryptoStatComponent implements OnInit {

  @Input() title: string | undefined;
  @Input() value: any | undefined;
  @Input() icon: string | undefined;
  @Input() persantage: string | undefined;
  @Input() profit: string | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
