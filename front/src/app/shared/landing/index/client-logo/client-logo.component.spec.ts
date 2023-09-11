import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ClientLogoComponent } from './client-logo.component';

describe('ClientLogoComponent', () => {
  let component: ClientLogoComponent;
  let fixture: ComponentFixture<ClientLogoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ClientLogoComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ClientLogoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
