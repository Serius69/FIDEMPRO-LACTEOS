import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-cover',
  templateUrl: './cover.component.html',
  styleUrls: ['./cover.component.scss']
})

/**
 * 404 Cover Component
 */
export class CoverComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
    document.documentElement.setAttribute('data-sidebar-size', 'lg');
  }

}
