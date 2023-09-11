import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmailBasicComponent } from './email-basic.component';

describe('EmailBasicComponent', () => {
  let component: EmailBasicComponent;
  let fixture: ComponentFixture<EmailBasicComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EmailBasicComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EmailBasicComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
