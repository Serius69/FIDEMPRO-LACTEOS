import { Component, OnInit } from '@angular/core';

import { TokenStorageService } from '../../../../core/services/token-storage.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})

/**
 * Profile Settings Component
 */
export class SettingsComponent implements OnInit {

  userData:any;

  constructor(private TokenStorageService : TokenStorageService) { }

  ngOnInit(): void {
    this.userData =  this.TokenStorageService.getUser();    
  }

  /**
  * Multiple Default Select2
  */
   selectValue = ['Illustrator', 'Photoshop', 'CSS', 'HTML', 'Javascript', 'Python', 'PHP'];

}
