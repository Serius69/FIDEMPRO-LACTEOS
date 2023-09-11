import { Component, OnInit } from '@angular/core';
import { interval } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-coming-soon',
  templateUrl: './coming-soon.component.html',
  styleUrls: ['./coming-soon.component.scss']
})

/**
 * ComingSoon Component
 */
export class ComingSoonComponent implements OnInit {

  // set the current year
  year: number = new Date().getFullYear();
  private _trialEndsAt: any;
  private _diff?: any;
  _days?: number;
  _hours?: number;
  _minutes?: number;
  _seconds?: number;

  constructor() { }

  ngOnInit(): void {
    document.documentElement.setAttribute('data-sidebar-size', 'lg');
    // Date Set
    this._trialEndsAt = "2023-12-31";

    /**
     * Count date set
     */
    interval(1000).pipe(map((x) => {
        this._diff = Date.parse(this._trialEndsAt) - Date.parse(new Date().toString());
    })).subscribe((x) => {
        this._days = this.getDays(this._diff);
        this._hours = this.getHours(this._diff);
        this._minutes = this.getMinutes(this._diff);
        this._seconds = this.getSeconds(this._diff);
    });
  }
 /**
   * Day Set
   */
  getDays(t: number) {
    return Math.floor(t / (1000 * 60 * 60 * 24));
  }

  /**
   * Hours Set
   */
  getHours(t: number) {
    return Math.floor((t / (1000 * 60 * 60)) % 24);
  }

  /**
   * Minutes set
   */
  getMinutes(t: number) {
    return Math.floor((t / 1000 / 60) % 60);
  }

  /**
   * Secound set
   */
  getSeconds(t: number) {
    return Math.floor((t / 1000) % 60);
  }

}
