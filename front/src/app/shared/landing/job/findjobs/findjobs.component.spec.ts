import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FindjobsComponent } from './findjobs.component';

describe('FindjobsComponent', () => {
  let component: FindjobsComponent;
  let fixture: ComponentFixture<FindjobsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ FindjobsComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FindjobsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
