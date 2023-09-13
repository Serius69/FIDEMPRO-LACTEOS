import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CrudVariableComponent } from './list.component';

describe('CrudVariableComponent', () => {
  let component: CrudVariableComponent;
  let fixture: ComponentFixture<CrudVariableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CrudVariableComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CrudVariableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
