import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RangeAreaComponent } from './range-area.component';

describe('RangeAreaComponent', () => {
  let component: RangeAreaComponent;
  let fixture: ComponentFixture<RangeAreaComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RangeAreaComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RangeAreaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
