export interface ListModel {
  id: string;
  logo: string;
  title: string;
  companyname: string;
  content: string;
  type: string;
  location: string;
  applied: string;
  date: string;
  tags?: Array<{}>;
  bookmark: boolean;
}