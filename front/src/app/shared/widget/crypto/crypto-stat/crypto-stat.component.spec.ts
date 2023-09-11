import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CryptoStatComponent } from './crypto-stat.component';

describe('CryptoStatComponent', () => {
  let component: CryptoStatComponent;
  let fixture: ComponentFixture<CryptoStatComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CryptoStatComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CryptoStatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
