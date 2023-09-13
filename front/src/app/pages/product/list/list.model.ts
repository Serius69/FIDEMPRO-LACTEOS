export interface projectListModel {
  id?: any;
  time?: string;
  img?: string;
  label?: string;
  caption?: string;
  number?: string;
  progressBar?: any;
  date?: string;
  users: Array<{
    name?: string;
    text?: string;
    profile?: string;
    variant?: string;
  }>;
  isIcon?: any;
}

export interface projectListModel1 {
  id?: any;
  label?: string;
  status?: string;
  statusClass?: string;
  deadline?: string;
  bg_color?: string;
  progressBar?: any;
  users: Array<{
    name?: string;
    text?: string;
    profile?: string;
    variant?: string;
  }>;
  isIcon?: any;
}

export interface projectListModel2 {
  id?: any;
  img?: string;
  label?: string;
  status?: string;
  statusClass?: string;
  deadline?: string;
  bg_color?: string;
  progressBar?: any;
  number?: any;
  users: Array<{
    name?: string;
    text?: string;
    profile?: string;
    variant?: string;
  }>;
  isIcon?: any;
}
