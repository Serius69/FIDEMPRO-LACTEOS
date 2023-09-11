export interface featuredModel {
  id: any;
  img: string;
  likes: string;
  title: string;
  category: string;
  highest: string;
  price?: any;
}

// Recent Model
export interface recentModel {
  id: any;
  img: string;
  title: string;
  category: string;
  icon: string;
  volume: string;
  hours?: any;
  creators: string;
  items: string;
  iconClass: string;
  color: string;
}

// Top Collection Model
export interface topCollectionModel {
  id: any;
  img: string;
  category: string;
  items: string;
}

// Popular Model
export interface popularModel {
  id: any;
  img: string;
  author: string;
  price: string;
}
