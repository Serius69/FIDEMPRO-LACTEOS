export interface Email {
  id: number;
  forId: any;
  unread?:any;
  name: string;
  number: string;
  subject: string;
  badge?:any;
  badgeClass?:any;
  teaser: string;
  date: string;
  type: string;
  category: string;
  label: string;
  img: string;
  isIcon?: any;
}
