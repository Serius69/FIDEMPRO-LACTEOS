export class FDP {
    private lambda: number;
  
    constructor(lambda: number) {
      this.lambda = lambda;
    }
  
    // Define your probability density function methods here
    calculateDensity(x: number): number {
      if (x >= 0) {
        return this.lambda * Math.exp(-this.lambda * x);
      } else {
        return 0;
      }
    }
  }
  