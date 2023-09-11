import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DealsStatusComponent } from './deals-status.component';

describe('DealsStatusComponent', () => {
  let component: DealsStatusComponent;
  let fixture: ComponentFixture<DealsStatusComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DealsStatusComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DealsStatusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
