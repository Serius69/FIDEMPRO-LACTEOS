import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EmailEcommerceComponent } from './email-ecommerce.component';

describe('EmailEcommerceComponent', () => {
  let component: EmailEcommerceComponent;
  let fixture: ComponentFixture<EmailEcommerceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EmailEcommerceComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EmailEcommerceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
