import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MyTaskComponent } from './my-task.component';

describe('MyTaskComponent', () => {
  let component: MyTaskComponent;
  let fixture: ComponentFixture<MyTaskComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MyTaskComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MyTaskComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
