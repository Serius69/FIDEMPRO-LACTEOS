import { Component, OnInit } from '@angular/core';
import {chatMessagesData} from "../../form/advanced/data";

@Component({
  selector: 'app-advanced',
  templateUrl: './advanced.component.html',
  styleUrls: ['./advanced.component.scss']
})

/**
 * Advanced Component
 */
export class AdvancedComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;

  constructor() { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Forms' },
      { label: 'Form Advanced', active: true }
    ];
  }

  /**
   * Default Select2
   */
   selectedAccount = 'This is a placeholder';
   public Default = chatMessagesData;

  keyword = 'name';
  // Fruit Data
  public Fruit = [
    {
      id: 1,
      name: 'Apple',
    },
    {
      id: 2,
      name: 'Banana',
    },
    {
      id: 3,
      name: 'Blueberry',
    },
    {
      id: 4,
      name: 'Cherry',
    },
    {
      id: 5,
      name: 'Coconut',
    },
    {
      id: 6,
      name: 'Kiwi',
    },
    {
      id: 7,
      name: 'Lemon',
    },
    {
      id: 8,
      name: 'Lime',
    },
    {
      id: 9,
      name: 'Mango',
    },
    {
      id: 10,
      name: 'Orange',
    }
  ];

  // Cars Data
  public Cars = [
    {
      id: 1,
      name: 'Chevrolet',
    },
    {
      id: 2,
      name: 'Fiat',
    },
    {
      id: 3,
      name: 'Ford',
    },
    {
      id: 4,
      name: 'Honda',
    },
    {
      id: 5,
      name: 'Hyundai',
    },
    {
      id: 6,
      name: 'Hyundai',
    },
    {
      id: 7,
      name: 'Kia',
    },
    {
      id: 8,
      name: 'Mahindra',
    },
    {
      id: 9,
      name: 'Maruti',
    },
    {
      id: 10,
      name: 'Mitsubishi',
    },
    {
      id: 11,
      name: 'MG',
    },
    {
      id: 12,
      name: 'Nissan',
    },
    {
      id: 13,
      name: 'Renault',
    },
    {
      id: 14,
      name: 'Skoda',
    },
    {
      id: 15,
      name: 'Tata',
    },
    {
      id: 16,
      name: 'Toyato',
    },
    {
      id: 17,
      name: 'Volkswagen',
    }
  ];

  selectEvent(item: any) {  }
  onChangeSearch(search: string) {}
  onFocused(e: any) { }

  
  // Default
  counter = 0;
  increment() {
    this.counter++;
  }
  
  decrement() {
    this.counter--;
  }
  
  // Light
  lightcounter = 5;
  lightincrement() {
    this.lightcounter++;
  }

  lightdecrement() {
    this.lightcounter--;
  }

  // Default Full
  defaultfullcounter = 4;
  defaultfulldecrement() {
    this.defaultfullcounter--;
  }

  defaultfullincrement() {
    this.defaultfullcounter++;
  }

  // Light Full
  lightfullcounter = 6;
  lightfulldecrement() {
    this.lightfullcounter--;
  }

  lightfullincrement() {
    this.lightfullcounter++;
  }

  // primary
  primarycounter = 6;
  primarydecrement() {
    this.primarycounter--;
  }

  primaryincrement() {
    this.primarycounter++;
  }

  // secondary
  secondarycounter = 1;
  secondarydecrement() {
    this.secondarycounter--;
  }

  secondaryincrement() {
    this.secondarycounter++;
  }

  // success
  successcounter = 4;
  successdecrement() {
    this.successcounter--;
  }

  successincrement() {
    this.successcounter++;
  }

  // Info
  infocounter = 1;
  infodecrement() {
    this.infocounter--;
  }

  infoincrement() {
    this.infocounter++;
  }

  // Warning
  warningcounter = 4;
  warningdecrement() {
    this.warningcounter--;
  }

  warningincrement() {
    this.warningcounter++;
  }

  // Danger
  dangercounter = 5;
  dangerdecrement() {
    this.dangercounter--;
  }

  dangerincrement() {
    this.dangercounter++;
  }

}
