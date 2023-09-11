export interface Todo {
  id?: any;
  task?: any;
  subItem?: Array<{}>;
  dueDate?: any;
  status?: any;
  priority?: any;
}


export interface Assigned {
  id: any;
  profile: any;
  name: any;
}

export interface project {
  id?: any;
  title?: any;
  coll?:any;
  subItem?: Array<{
    version?: any;
    color?: any;
  }>;
}
