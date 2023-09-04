import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-footer',
  templateUrl: './footer.component.html'
})
export class FooterComponent implements OnInit {
  currentYear: number; // Declare currentYear property

  constructor() {
    this.currentYear = new Date().getFullYear(); // Calculate current year
  }

  ngOnInit(): void {
  }
}
