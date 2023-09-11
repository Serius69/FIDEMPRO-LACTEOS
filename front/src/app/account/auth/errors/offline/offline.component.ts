import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-offline',
  templateUrl: './offline.component.html',
  styleUrls: ['./offline.component.scss']
})

/**
 * Offline Component
 */
export class OfflineComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
    document.documentElement.setAttribute('data-sidebar-size', 'lg');
  }

}
