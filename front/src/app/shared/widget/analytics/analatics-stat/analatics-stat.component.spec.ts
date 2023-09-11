import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalaticsStatComponent } from './analatics-stat.component';

describe('AnalaticsStatComponent', () => {
  let component: AnalaticsStatComponent;
  let fixture: ComponentFixture<AnalaticsStatComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AnalaticsStatComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AnalaticsStatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
