import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-crm-stat',
  templateUrl: './crm-stat.component.html',
  styleUrls: ['./crm-stat.component.scss']
})

/**
 * Crm Stat Component
 */
export class CrmStatComponent implements OnInit {

  @Input() title: string | undefined;
  @Input() value: any | undefined;
  @Input() icon: string | undefined;
  @Input() profit: string | undefined;
  @Input() sign: string | undefined;
  @Input() percentage: string | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
