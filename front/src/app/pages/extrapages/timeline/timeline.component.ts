import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

// Swiper Slider
import { SwiperOptions } from 'swiper';

@Component({
  selector: 'app-timeline',
  templateUrl: './timeline.component.html',
  styleUrls: ['./timeline.component.scss']
})

/**
 * Timeline Component
 */
export class TimelineComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Pages' },
      { label: 'Timeline', active: true }
    ];
  }

    /**
   * Swiper setting
   */
     config = {
      initialSlide: 0,
      slidesPerView: 1,
      breakpoints:{
        768:{
          slidesPerView: 2, 
        },
        1200:{
          slidesPerView: 5, 
        }
      }
    };


}
