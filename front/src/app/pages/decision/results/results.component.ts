import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html'
})
export class ResultsComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

  earnings = [
    { title: 'Expense 1', amount: 50, date: '2023-08-28' },
    { title: 'Expense 2', amount: 75, date: '2023-08-29' },
    // ... other expenses
  ];
  sales = [
    { title: 'Expense 1', amount: 50, date: '2023-08-28' },
    { title: 'Expense 2', amount: 75, date: '2023-08-29' },
    // ... other expenses
  ];
  profit = [
    { name: 'Supporter 1', amount: 100 },
    { name: 'Supporter 2', amount: 200 },
    // ... other supporters
  ];
  expenses = [
    { title: 'Expense 1', amount: 50, date: '2023-08-28' },
    { title: 'Expense 2', amount: 75, date: '2023-08-29' },
    // ... other expenses
  ];

    total_expense = this.expenses.reduce((total, expense) => total + expense.amount, 0);
    total_earning = this.earnings.reduce((total, earnings) => total + earnings.amount, 0);
    total_sale = this.sales.reduce((total, sales) => total + sales.amount, 0);
    total_profit = this.profit.reduce((total, expenses) => total + expenses.amount, 0);
}
