/**
 * Todo List
 */
 export interface Task {
  id: string;
  title: string;
  date: string;
  content: string;
  progress: any;
  roles: Array<{}>;
  users: Array<{
      name?: string;
      profile?: string;
  }>;
  view: string;
  comment: string;
  pin: string;
  status: string;
  variant?: string;
}
