import { DataNumber } from './result';
import { DataStringNumber } from './result';
import { DataStringStringNumber } from './result';

describe('Result', () => {
  it('should create an instance', () => {
    expect(new DataNumber()).toBeTruthy();
  });
  it('should create an instance', () => {
    expect(new DataStringNumber()).toBeTruthy();
  });
  it('should create an instance', () => {
    expect(new DataStringStringNumber()).toBeTruthy();
  });
});
