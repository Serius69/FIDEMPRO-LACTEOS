export interface ContactsModel {
  profile: string;
  name: string;
  company: string;
  email: string;
  phone: string;
  score: string;
  date: string;
  time: string;
  tags: Array<{}>;
  isSelected?:any;
}
