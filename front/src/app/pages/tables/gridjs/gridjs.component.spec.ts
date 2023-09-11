import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GridjsComponent } from './gridjs.component';

describe('GridjsComponent', () => {
  let component: GridjsComponent;
  let fixture: ComponentFixture<GridjsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ GridjsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GridjsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
