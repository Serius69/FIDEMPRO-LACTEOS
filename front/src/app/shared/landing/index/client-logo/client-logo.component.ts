import { Component, OnInit } from '@angular/core';

// Swiper Slider
import { SwiperOptions } from 'swiper';

import {clientLogoModel} from './client-logo.module';
import { ClientLogo } from './data';

@Component({
  selector: 'app-client-logo',
  templateUrl: './client-logo.component.html',
  styleUrls: ['./client-logo.component.scss']
})

/**
 * ClientLogoComponent
 */
export class ClientLogoComponent implements OnInit {

  constructor() { }

  ClientLogo!: clientLogoModel[];

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
    this.ClientLogo = ClientLogo;
  }

  /**
   * Swiper Responsive setting
   */
   public Responsive: SwiperOptions = {
    slidesPerView: 1,
    pagination: true,
    mousewheel: true,
    breakpoints:{
      768:{
        slidesPerView: 2, 
      },
      1200:{
        slidesPerView: 4, 
      }
    }
  };

}
