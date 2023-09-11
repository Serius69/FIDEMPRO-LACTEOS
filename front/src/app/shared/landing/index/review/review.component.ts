import { Component, OnInit } from '@angular/core';

import { SwiperOptions } from 'swiper';

import {clientLogoModel} from './review.module';
import { ClientLogo } from './data';


@Component({
  selector: 'app-review',
  templateUrl: './review.component.html',
  styleUrls: ['./review.component.scss']
})

/**
 * Review Component
 */
export class ReviewComponent implements OnInit {

  ClientLogo!: clientLogoModel[];
  
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
      this.ClientLogo = ClientLogo;
    }

  /**
   * Swiper Responsive setting
   */
   public review: SwiperOptions = {
    initialSlide: 0,
    slidesPerView: 1,
    pagination: true,
    navigation: true
  };

}
