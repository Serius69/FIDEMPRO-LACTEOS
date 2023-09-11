import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { DataService } from 'src/app/services/data.service';

@Component({
  selector: 'app-simulate',
  templateUrl: './simulate.component.html'
})
export class SimulateComponent implements OnInit {
  selectedScenario: string = ''; // Initialize with an empty string or default value
  selectedTimeUnit: string = ''; // Initialize with an empty string or default value
  startDate: string = ''; // Initialize with an empty string or default value
  endDate: string = ''; // Initialize with an empty string or default value
  lambda: number = 0.5;

  submitForm() {
    // Handle form submission logic here
    console.log('Scenario:', this.selectedScenario);
    console.log('Time Unit:', this.selectedTimeUnit);
    console.log('Start Date:', this.startDate);
    console.log('End Date:', this.endDate);
    // You can perform further actions like making API requests, processing data, etc.
  }
  constructor(private http: HttpClient, private dataService: DataService) {}

  ngOnInit(): void {
  }

  calcularFDP(x: number): number {
    if (x >= 0) {
      return this.lambda * Math.exp(-this.lambda * x);
    } else {
      return 0;
    }
  }

  calcularKS(){


  }

}
