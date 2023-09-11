/**
 * Folder Model List
 */
export interface FolderModel {
  id: any;
  title: string;
  files: string;
  gb: string;
}

/**
 * Recent Model List
 */
 export interface recentModel {
  id: any;
  icon: string;
  icon_color: string;
  icon_name: string;
  item: string;
  size: string;
  type: string;
  date: string;
  isIcon?:any;
}