import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectsStatComponent } from './projects-stat.component';

describe('ProjectsStatComponent', () => {
  let component: ProjectsStatComponent;
  let fixture: ComponentFixture<ProjectsStatComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ProjectsStatComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ProjectsStatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
