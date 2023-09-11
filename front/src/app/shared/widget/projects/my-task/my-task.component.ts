import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-my-task',
  templateUrl: './my-task.component.html',
  styleUrls: ['./my-task.component.scss']
})

/**
 * MyTask Component
 */
export class MyTaskComponent implements OnInit {

  // Upcoming Activities
  @Input() MyTask: Array<{
    name?: string;
    dedline?: string;
    status?: string;
    assignee: {
      name?: string;
      profile?: string;
    };
  }> | undefined;

  constructor() { }

  ngOnInit(): void {
  }

}
