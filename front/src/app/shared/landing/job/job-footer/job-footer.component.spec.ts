import { ComponentFixture, TestBed } from '@angular/core/testing';

import { JobFooterComponent } from './job-footer.component';

describe('JobFooterComponent', () => {
  let component: JobFooterComponent;
  let fixture: ComponentFixture<JobFooterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ JobFooterComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(JobFooterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
