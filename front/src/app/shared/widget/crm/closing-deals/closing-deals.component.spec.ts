import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ClosingDealsComponent } from './closing-deals.component';

describe('ClosingDealsComponent', () => {
  let component: ClosingDealsComponent;
  let fixture: ComponentFixture<ClosingDealsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ClosingDealsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ClosingDealsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
