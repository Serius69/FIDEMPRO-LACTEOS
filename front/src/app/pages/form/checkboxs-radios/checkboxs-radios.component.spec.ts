import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CheckboxsRadiosComponent } from './checkboxs-radios.component';

describe('CheckboxsRadiosComponent', () => {
  let component: CheckboxsRadiosComponent;
  let fixture: ComponentFixture<CheckboxsRadiosComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CheckboxsRadiosComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CheckboxsRadiosComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
