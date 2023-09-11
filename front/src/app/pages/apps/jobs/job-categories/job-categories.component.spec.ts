import { ComponentFixture, TestBed } from '@angular/core/testing';

import { JobCategoriesComponent } from './job-categories.component';

describe('JobCategoriesComponent', () => {
  let component: JobCategoriesComponent;
  let fixture: ComponentFixture<JobCategoriesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ JobCategoriesComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(JobCategoriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
