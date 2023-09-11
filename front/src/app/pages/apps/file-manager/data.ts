/**
 * folder List
 */
const folderData = [
  {
    id:1,  
    title: 'Projects',
    files: '349',
    gb: '4.10'
  },
  {
    id:2,
    title: 'Documents',
    files: '2348',
    gb: '27.01'
  },
  {
    id:3,
    title: 'Media',
    files: '12480',
    gb: '20.87'
  },
  {
    id:4,
    title: 'Velzon v1.7.0',
    files: '180',
    gb: '478.65'
  },
];

/**
 * Recent Data List
 */
 const recentData = [
  {
    id:1,  
    icon: 'ri-gallery-fill',
    icon_color:"success",
    icon_name: 'logo-dark.png',
    item: '01',
    size: '1.3 MB',
    type:"Media",
    date: '24 May, 2022',
  },
  {
    id:2,  
    icon: 'ri-file-pdf-fill',
    icon_color:"danger",
    icon_name: 'velzon-invoice.pdf',
    item: '01',
    size: '1.1 MB',
    type:"Documents",
    date: '05 May, 2022',
    isIcon: true
  },
  {
    id:3,  
    icon: 'ri-folder-2-fill',
    icon_color:"warning",
    icon_name: 'Velzon React',
    item: '367',
    size: '934 MB',
    type:"Media",
    date: '28 Apr, 2022',
  },
  {
    id:4,  
    icon: 'ri-file-text-fill',
    icon_color:"secondary",
    icon_name: 'html.docx',
    item: '01',
    size: '0.3 KB',
    type:"Documents",
    date: '19 Apr, 2022',
  },
  {
    id:5,  
    icon: 'ri-gallery-fill',
    icon_color:"success",
    icon_name: 'default.jpg',
    item: '01',
    size: '0.7 MB',
    type:"Media",
    date: '	06 Apr, 2022',
    isIcon: true
  },
  {
    id:6,  
    icon: 'ri-file-text-fill',
    icon_color:"secondary",
    icon_name: 'html.docx',
    item: '01',
    size: '0.3 KB',
    type:"Recent",
    date: '19 Apr, 2022',
  },
  {
    id:7,  
    icon: 'ri-gallery-fill',
    icon_color:"success",
    icon_name: 'default.jpg',
    item: '01',
    size: '0.7 MB',
    type:"Important",
    date: '	06 Apr, 2022',
    isIcon: true
  },
  {
    id:8,  
    icon: 'ri-folder-2-fill',
    icon_color:"warning",
    icon_name: 'Velzon React',
    item: '367',
    size: '934 MB',
    type:"Deleted",
    date: '28 Apr, 2022',
  },
];

export { folderData, recentData };