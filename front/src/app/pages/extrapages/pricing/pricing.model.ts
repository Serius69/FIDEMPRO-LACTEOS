/**
 * Monthly Plan
 */
 export interface MonthlyPlanModel {
  id: any;
  type: string;
  rate?: number;
  description?: string;
  projects: any;
  Customers: any;
  FTP?: any;
  supportClass?: any;
  supportClassSymbol?: any;
  storageClass?: any;
  storageClassSymbol?: any;
  domainClass?: any;
  domainClassSymbol?: any;
  ribbon?: any;
  planButtonClassname?: any;
}

/**
 * Yearly Plan
 */
 export interface YearlyPlanModel {
  id: any;
  type: string;
  rate?: number;
  price?: number;
  description?: string;
  projects: any;
  Customers: any;
  FTP?: any;
  supportClass?: any;
  supportClassSymbol?: any;
  storageClass?: any;
  storageClassSymbol?: any;
  domainClass?: any;
  domainClassSymbol?: any;
  ribbon?: any;
  planButtonClassname?: any;
}

/**
 * Choose Plan
 */
 export interface PricingModel {
  id : any,
  type :any,
  purpose :any,
  planIcon:any,
  rate : any,
  projects : any,
  Customers :any,
  FTP:any,
  supportClass:any,
  supportClassSymbol :any,
  storageClass :any,
  storageClassSymbol :any,
  domainClass :any,
  domainClassSymbol :any,
  ribbon:any,
  planButtonClassname: any
}

/**
 * Simple Plan
 */
 export interface SimpleModel {
  id : any,
  type :string,
  purpose :string,
  rate : number,
  users : number,
  storage : String,
  domain:string,
  support:string,
  ribbon:any
}
