import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
// variables Services
import { restApiService } from "../../../core/services/rest-api.service";

// Swiper Slider
import { SwiperOptions } from 'swiper';
import { Variable, variableList } from 'src/app/core/common/variable';

@Component({
  selector: 'app-overview',
  templateUrl: './overview.component.html'
})

/**
 * variableDetail Component
 */
export class OverviewComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  public variableDetail!: Variable[];
  defaultSelect = 2;
  readonly = false;
  content?: any;
  variables: any;

  constructor(private route: ActivatedRoute, private modalService: NgbModal, public restApiService: restApiService) {
    this.variables = this.route.snapshot.params
    this.route.params.subscribe(params =>
      this.variableDetail = variableList.filter(function (variable) {
        return variable.id == parseInt(params['any'])
      })
    );
  }

  ngOnInit(): void {
    /**
   * BreadCrumb
   */
    this.breadCrumbItems = [
      { label: 'Ecommerce' },
      { label: 'variable Details', active: true }
    ];
  }

  /**
   * Swiper setting
   */
  config: SwiperOptions = {
    pagination: { el: '.swiper-pagination', clickable: true },
    navigation: {
      nextEl: '.swiper-button-next',
      prevEl: '.swiper-button-prev'
    },
    spaceBetween: 30
  };

}