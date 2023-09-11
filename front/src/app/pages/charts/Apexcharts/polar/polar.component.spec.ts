import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PolarComponent } from './polar.component';

describe('PolarComponent', () => {
  let component: PolarComponent;
  let fixture: ComponentFixture<PolarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PolarComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PolarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
