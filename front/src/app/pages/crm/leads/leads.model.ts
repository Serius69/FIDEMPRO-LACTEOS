export interface LeadsModel {
  profile: string;
  name: string;
  company: string;
  score: string;
  phone: string;
  location: string;
  date: string;
  tags: Array<{}>;
  isSelected?:any;
}
