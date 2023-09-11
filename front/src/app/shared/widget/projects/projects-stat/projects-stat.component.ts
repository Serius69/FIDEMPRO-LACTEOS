import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-projects-stat',
  templateUrl: './projects-stat.component.html',
  styleUrls: ['./projects-stat.component.scss']
})

/**
 * Projects Stat Component
 */
export class ProjectsStatComponent implements OnInit {

  @Input() title: string | undefined;
  @Input() value: any | undefined;
  @Input() icon: string | undefined;
  @Input() persantage: string | undefined;
  @Input() profit: string | undefined;
  @Input() month: string | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
