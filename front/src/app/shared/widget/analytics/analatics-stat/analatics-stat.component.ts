import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-analatics-stat',
  templateUrl: './analatics-stat.component.html',
  styleUrls: ['./analatics-stat.component.scss']
})

/**
 * Analatics stat Component
 */
export class AnalaticsStatComponent implements OnInit {

  @Input() title: string | undefined;
  @Input() value: any | undefined;
  @Input() icon: string | undefined;
  @Input() persantage: string | undefined;
  @Input() profit: string | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
