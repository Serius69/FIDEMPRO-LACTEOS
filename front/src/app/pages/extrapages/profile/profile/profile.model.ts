export interface projectListModel {
  title?: any;
  updatedTime?: any;
  badgeText ?: any;
  badgeClass?: any;
  member?: Array<{
    name?: any;
    text?: any;
    img?: any;
    variant?: any;
  }>;
  cardBorderColor?:string;
}

export interface documentModel {
  id:any,
  icon:string,
  iconBackgroundClass:string,
  fileName:string,
  fileType:string,
  fileSize:string,
  updatedDate:string
}
