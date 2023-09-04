import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-simulate',
  templateUrl: './simulate.component.html'
})
export class SimulateComponent implements OnInit {
  selectedScenario: string = ''; // Initialize with an empty string or default value
  selectedTimeUnit: string = ''; // Initialize with an empty string or default value
  startDate: string = ''; // Initialize with an empty string or default value
  endDate: string = ''; // Initialize with an empty string or default value

  submitForm() {
    // Handle form submission logic here
    console.log('Scenario:', this.selectedScenario);
    console.log('Time Unit:', this.selectedTimeUnit);
    console.log('Start Date:', this.startDate);
    console.log('End Date:', this.endDate);
    // You can perform further actions like making API requests, processing data, etc.
  }
  constructor() { }

  ngOnInit(): void {
  }

}
