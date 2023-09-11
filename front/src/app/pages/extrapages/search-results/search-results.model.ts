/**
 * Swiper List
 */
 export interface swiperModel {
  id: any;
  img?: any;
  title?: any;
}

/**
 * Gallery List
 */
 export interface GalleryModel {
  id:any,
  img:string,
  title:string,
  auther:string,
  likes:string,
  comments:string
}

/**
 * News List
 */
 export interface NewsModel {
  id:any,
  img:string,
  badgeClass:string,
  badgeText:string,
  title:string,
  auther:string,
  date:string
}

/**
 * Video List
 */
 export interface VideoModel {
  id:any,
  title:string,
  siteLink:string,
  videoLink : any,
  description :string,
  likes:number,
  comments:number,
  auther :string
}
