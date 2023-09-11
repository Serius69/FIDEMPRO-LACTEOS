import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-cover',
  templateUrl: './cover.component.html',
  styleUrls: ['./cover.component.scss']
})

/**
 * Logout Cover Component
 */
export class CoverComponent implements OnInit {

  // set the current year
  year: number = new Date().getFullYear();
  // Carousel navigation arrow show
  showNavigationArrows: any;

  constructor() { }

  ngOnInit(): void {
  }

}
