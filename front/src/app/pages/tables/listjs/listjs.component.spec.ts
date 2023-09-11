import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ListjsComponent } from './listjs.component';

describe('ListjsComponent', () => {
  let component: ListjsComponent;
  let fixture: ComponentFixture<ListjsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ListjsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ListjsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
