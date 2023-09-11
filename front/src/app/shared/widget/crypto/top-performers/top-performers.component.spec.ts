import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TopPerformersComponent } from './top-performers.component';

describe('TopPerformersComponent', () => {
  let component: TopPerformersComponent;
  let fixture: ComponentFixture<TopPerformersComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TopPerformersComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TopPerformersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
