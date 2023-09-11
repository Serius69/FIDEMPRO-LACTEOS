import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NouserComponent } from './nouser.component';

describe('NouserComponent', () => {
  let component: NouserComponent;
  let fixture: ComponentFixture<NouserComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ NouserComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(NouserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
