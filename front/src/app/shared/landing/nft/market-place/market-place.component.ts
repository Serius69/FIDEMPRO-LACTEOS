import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-market-place',
  templateUrl: './market-place.component.html',
  styleUrls: ['./market-place.component.scss']
})

/**
 * Market-Place Component
 */
export class MarketPlaceComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
    /**
     * fetches data
     */
     this.filterredImages = this.list;
  }

  /**
   * Portfolio Modern Data
   */
   filterredImages: { image: string; like?: string; title: string; sub_title: string; highest: string; eth: string; category: string;}[] | undefined;
   galleryFilter = 'allItems';
   list = [{
      image: 'assets/images/nft/img-03.jpg',
      like: '19.29',
      title: "Creative Filtered Portrait",
      sub_title: "Photography",
      highest: '75.3',
      eth: '67.36',
      category: 'artWork'
    },
    {
      image: 'assets/images/nft/img-02.jpg',
      like: '23.63',
      title: "The Chirstoper",
      sub_title: "Music",
      highest: '412.30',
      eth: '394.7',
      category: 'music'
    },
    {
      image: 'assets/images/nft/gif/img-4.gif',
      like: '15.93',
      title: "Evolved Reality",
      sub_title: "Video",
      highest: '2.75',
      eth: '3.167',
      category: 'games'
    },
    {
      image: 'assets/images/nft/img-01.jpg',
      like: '14.85',
      title: "Abstract Face Painting",
      sub_title: "Collectibles",
      highest: '122.34',
      eth: '97.8',
      category: 'crypto-card'
    },
    {
      image: 'assets/images/nft/img-05.jpg',
      like: '64.10',
      title: "Long-tailed Macaque",
      sub_title: "Artwork",
      highest: '874.01',
      eth: '745.14',
      category: '3d-style'
    },
    {
      image: 'assets/images/nft/img-06.jpg',
      like: '36.42',
      title: "Robotic Body Art",
      sub_title: "Artwork",
      highest: '41.658',
      eth: '34.81',
      category: 'artWork'
    },
   ];


  /***
  * Active all category selected
  */
  activeCategory(category: string) {
    this.galleryFilter = category;
    if (this.galleryFilter === 'allItems') {
      this.filterredImages = this.list;
    } else {
      this.filterredImages = this.list.filter(x => x.category === this.galleryFilter);
    }
  }

}
