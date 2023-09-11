import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-button-settings',
  templateUrl: './button-settings.component.html'
})
export class ButtonSettingsComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

  topFunction() {
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE, and Opera
  }

}
