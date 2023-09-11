import { Component, OnInit } from '@angular/core';
// Light Box
import { Lightbox } from 'ngx-lightbox';

@Component({
  selector: 'app-gallery',
  templateUrl: './gallery.component.html',
  styleUrls: ['./gallery.component.scss']
})

/**
 * Gallery Component
 */
export class GalleryComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  images: { src: string; thumb: string; caption: string }[] = [];

  constructor(private lightbox: Lightbox) {
    for (let i = 1; i <= 24; i++) {
      const src = '../../../../assets/images/small/img-' + i + '.jpg';
      const caption = 'Image ' + i + ' caption here';
      const thumb = '../../../../assets/images/small/img-' + i + '-thumb.jpg';
      const item = {
        src: src,
        caption: caption,
        thumb: thumb
      };
      this.images.push(item);
    }
  }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
     this.breadCrumbItems = [
      { label: 'Pages' },
      { label: 'Gallery', active: true }
    ];

    this.filterredImages = this.list;
  }

  /**
   * Portfolio Classic Two Data
   */
   filterredImages: { img: string; title: string; auther: string; likes: string; comments: string; category: string; }[] | undefined;
   galleryFilter = 'all';
   list = [ {
      id:1,
      img:'assets/images/small/img-1.jpg',
      title:"Glasses and laptop from above",
      auther:"Ron Mackie",
      likes:"2.2K",
      comments:"1.3K",
      category: 'project'
    },
    {
      id:3,
      img:'assets/images/small/img-3.jpg',
      title:"Photo was taken in Beach",
      auther:"Elwood Arter",
      likes:"2.2K",
      comments:"1.3K",
      category: 'project'
    },
    {
      id:4,
      img:'assets/images/small/img-4.jpg',
      title:"Drawing a sketch",
      auther:"Jason McQuaid",
      likes:"2.2K",
      comments:"1.3K",
      category: 'project'
    },
    {
      id:5,
      img:'assets/images/small/img-5.jpg',
      title:"Working from home little spot",
      auther:"Henry Baird",
      likes:"2.2K",
      comments:"1.3K",
      category: 'project'
    },
    {
      id:6,
      img:'assets/images/small/img-7.jpg',
      title:"Sunrise above a beach",
      auther:"James Ballard",
      likes:"2.2K",
      comments:"1.3K",
      category: 'project'
    },
    {
      id:7,
      img:'assets/images/small/img-9.jpg',
      title:"Dramatic clouds at the Golden Gate Bridge",
      auther:"Ron Mackie",
      likes:"2.2K",
      comments:"1.3K",
      category: 'project'
    },
    {
      id:8,
      img:'assets/images/small/img-10.jpg',
      title:"Fun day at the Hill Station",
      auther:"Henry Baird",
      likes:"2.2K",
      comments:"1.3K",
      category: 'project'
    },
    {
      id:9,
      img:'assets/images/small/img-1.jpg',
      title:"Glasses and laptop from above",
      auther:"Ron Mackie",
      likes:"2.2K",
      comments:"1.3K",
      category: 'designing'
    },
    {
      id:10,
      img:'assets/images/small/img-4.jpg',
      title:"Drawing a sketch",
      auther:"Jason McQuaid",
      likes:"2.2K",
      comments:"1.3K",
      category: 'designing'
    },
    {
      id:11,
      img:'assets/images/small/img-5.jpg',
      title:"Working from home little spot",
      auther:"Henry Baird",
      likes:"2.2K",
      comments:"1.3K",
      category: 'designing'
    },
    {
      id:12,
      img:'assets/images/small/img-7.jpg',
      title:"Sunrise above a beach",
      auther:"James Ballard",
      likes:"2.2K",
      comments:"1.3K",
      category: 'designing'
    },
    {
      id:13,
      img:'assets/images/small/img-9.jpg',
      title:"Dramatic clouds at the Golden Gate Bridge",
      auther:"Ron Mackie",
      likes:"2.2K",
      comments:"1.3K",
      category: 'designing'
    },
    {
      id:14,
      img:'assets/images/small/img-10.jpg',
      title:"Fun day at the Hill Station",
      auther:"Henry Baird",
      likes:"2.2K",
      comments:"1.3K",
      category: 'designing'
    },
    {
      id:15,
      img:'assets/images/small/img-2.jpg',
      title:"Working at a coffee shop",
      auther:"Nancy Martino",
      likes:"2.2K",
      comments:"1.3K",
      category: 'photography'
    },
    {
      id:16,
      img:'assets/images/small/img-6.jpg',
      title:"Project discussion with team",
      auther:"Ruby Griffin",
      likes:"2.2K",
      comments:"1.3K",
      category: 'photography'
    },
    {
      id:17,
      img:'assets/images/small/img-8.jpg',
      title:"Glasses and laptop from above",
      auther:"Erica Kernan",
      likes:"2.2K",
      comments:"1.3K",
      category: 'photography'
    },
    {
      id:18,
      img:'assets/images/small/img-11.jpg',
      title:"Cycling in the countryside",
      auther:"Nancy Martino",
      likes:"2.2K",
      comments:"1.3K",
      category: 'photography'
    },
    {
      id:19,
      img:'assets/images/small/img-12.jpg',
      title:"A mix of friends and strangers heading off to find an adventure.",
      auther:"Erica Kernan",
      likes:"2.2K",
      comments:"1.3K",
      category: 'photography'
    },
    {
      id:20,
      img:'assets/images/small/img-1.jpg',
      title:"Glasses and laptop from above",
      auther:"Ron Mackie",
      likes:"2.2K",
      comments:"1.3K",
      category: 'development'
    },
    {
      id:21,
      img:'assets/images/small/img-3.jpg',
      title:"Photo was taken in Beach",
      auther:"Elwood Arter",
      likes:"2.2K",
      comments:"1.3K",
      category: 'development'
    },
    {
      id:22,
      img:'assets/images/small/img-7.jpg',
      title:"Sunrise above a beach",
      auther:"James Ballard",
      likes:"2.2K",
      comments:"1.3K",
      category: 'development'
    },
    {
      id:23,
      img:'assets/images/small/img-9.jpg',
      title:"Dramatic clouds at the Golden Gate Bridge",
      auther:"Ron Mackie",
      likes:"2.2K",
      comments:"1.3K",
      category: 'development'
    },
   ];

   /***
   * Active all category selected
   */
  activeCategory(category: string) {
    this.galleryFilter = category;
    if (this.galleryFilter === 'all') {
      this.filterredImages = this.list;
    } else {
      this.filterredImages = this.list.filter(x => x.category === this.galleryFilter);
    }
  }

  open(index: number): void {
    // open lightbox
    this.lightbox.open(this.images, index, { });
  }

  close(): void {
    // close lightbox programmatically
    this.lightbox.close();
  }


}
