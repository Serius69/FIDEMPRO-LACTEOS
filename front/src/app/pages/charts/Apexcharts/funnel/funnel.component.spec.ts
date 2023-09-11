import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FunnelComponent } from './funnel.component';

describe('FunnelComponent', () => {
  let component: FunnelComponent;
  let fixture: ComponentFixture<FunnelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FunnelComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FunnelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
