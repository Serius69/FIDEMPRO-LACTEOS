import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ApikeyComponent } from './apikey.component';

describe('ApikeyComponent', () => {
  let component: ApikeyComponent;
  let fixture: ComponentFixture<ApikeyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ApikeyComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ApikeyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
