import { Component, OnInit } from '@angular/core';

import { SwiperOptions } from 'swiper';

import {clientLogoModel} from './categories.model';
import { ClientLogo } from './data';

@Component({
  selector: 'app-categories',
  templateUrl: './categories.component.html',
  styleUrls: ['./categories.component.scss']
})

/**
 * Categories Component
 */
export class CategoriesComponent implements OnInit {

  ClientLogo!: clientLogoModel[];

  constructor() { }

  ngOnInit(): void {
    /**
     * fetches data
     */
     this._fetchData();
  }

  /**
 * Trending All Categories
 */
   private _fetchData() {
    this.ClientLogo = ClientLogo;
  }

  /**
   * Swiper Responsive setting
   */
   public Responsive: SwiperOptions = {
    slidesPerView: 1,
     pagination: {
      el: '.swiper-pagination',
      clickable: true,
    },
    // mousewheel: true,
    navigation: true,
    spaceBetween: 25,
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
