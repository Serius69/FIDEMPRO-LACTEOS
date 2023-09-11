import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NftStatComponent } from './nft-stat.component';

describe('NftStatComponent', () => {
  let component: NftStatComponent;
  let fixture: ComponentFixture<NftStatComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NftStatComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NftStatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
