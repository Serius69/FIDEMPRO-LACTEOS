import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PassCreateComponent } from './pass-create.component';

describe('PassCreateComponent', () => {
  let component: PassCreateComponent;
  let fixture: ComponentFixture<PassCreateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ PassCreateComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PassCreateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
