import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TopCreatorComponent } from './top-creator.component';

describe('TopCreatorComponent', () => {
  let component: TopCreatorComponent;
  let fixture: ComponentFixture<TopCreatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TopCreatorComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TopCreatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
