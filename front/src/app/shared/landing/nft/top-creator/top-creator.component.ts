import { Component, OnInit } from '@angular/core';

import {creatorModel} from './top-creator.model';
import { creatorData } from './data';

@Component({
  selector: 'app-top-creator',
  templateUrl: './top-creator.component.html',
  styleUrls: ['./top-creator.component.scss']
})

/**
 * TopCreator Component
 */
export class TopCreatorComponent implements OnInit {

  creatorData!: creatorModel[];

  constructor() { }

  ngOnInit(): void {
    this.creatorData = creatorData;
  }

}
