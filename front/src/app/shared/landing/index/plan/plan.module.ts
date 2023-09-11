/**
 * Monthly Plan
 */
 export interface MonthlyPlanModel {
    id: any;
    title: string;
    subTitle: string;
    icon: string;
    rate?: number;
    projects: any;
    Customers: any;
    band: any;
    FTP?: any;
    supportClass?: any;
    supportClassSymbol?: any;
    storageClass?: any;
    storageClassSymbol?: any;
    domainClass?: any;
    domainClassSymbol?: any;
    ribbon?: any;
  }

  /**
 * Annual Plan
 */
 export interface AnnualPlanModel {
  id: any;
  title: string;
  subTitle: string;
  icon: string;
  rate?: number;
  projects: any;
  Customers: any;
  band: any;
  FTP?: any;
  supportClass?: any;
  supportClassSymbol?: any;
  storageClass?: any;
  storageClassSymbol?: any;
  domainClass?: any;
  domainClassSymbol?: any;
  ribbon?: any;
}