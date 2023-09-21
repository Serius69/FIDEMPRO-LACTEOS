import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-success-msg',
  templateUrl: './success-msg.component.html'
})

/**
 * Success Msg SuccessMsg Component
 */
export class SuccessMsgComponent implements OnInit {

  // set the current year
  year: number = new Date().getFullYear();
  // Carousel navigation arrow show
  showNavigationArrows: any;

  constructor() { }

  ngOnInit(): void {
  }

}
