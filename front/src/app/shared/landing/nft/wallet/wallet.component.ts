import { Component, OnInit } from '@angular/core';

import {walletModel} from './wallet.model';
import { walletData } from './data';

@Component({
  selector: 'app-wallet',
  templateUrl: './wallet.component.html',
  styleUrls: ['./wallet.component.scss']
})

/**
 * Wallet Component
 */
export class WalletComponent implements OnInit {

  walletData!: walletModel[];

  constructor() { }

  ngOnInit(): void {
    /**
     * fetches data
     */
     this._fetchData();
  }

  /**
  * User grid data fetches
  */
   private _fetchData() {
    this.walletData = walletData;
  }

}
