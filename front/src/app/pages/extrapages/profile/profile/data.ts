/**
 * Project List Data
 */
const projectList = [
  {
      title: "Chat App Update",
      updatedTime: '2 year Ago',
      badgeText: 'Inprogress',
      badgeClass: 'warning',
      member : [
          {
            img: 'assets/images/users/avatar-1.jpg'
          },
          {
            img: 'assets/images/users/avatar-3.jpg'
          },
          {
            text: 'J',
            variant: 'bg-light text-primary'
          },
        ],
      cardBorderColor: 'warning',
  },
  {
    title: "ABC Project Customization",
    updatedTime:"2 month Ago",
    badgeText :"Progress",
    badgeClass:"primary",
    member : [
      {
        img:'assets/images/users/avatar-8.jpg'
      },
      {
        img:'assets/images/users/avatar-7.jpg'
      },
      {
        img:'assets/images/users/avatar-6.jpg'
      },
      {
        text: '2+',
        variant: 'bg-primary'
      },
    ],
    cardBorderColor:"success",
  },
  {
    title: "Client - Frank Hook",
    updatedTime:"1 hr Ago",
    badgeText :"New",
    badgeClass:"info",
    member : [
      {
        img:'assets/images/users/avatar-4.jpg'
      },
      {
        text: 'M',
        variant: 'bg-light text-primary'
      },
      {
        img:'assets/images/users/avatar-3.jpg'
      }
    ],
    cardBorderColor:"info",
  },
];

/**
 * Document Data
 */
const document=[
  {
      id:1,
      icon:"ri-file-zip-fill",
      iconBackgroundClass:"primary",
      fileName:"Artboard-documents.zip",
      fileType:"Zip File",
      fileSize:"4.57 MB",
      updatedDate:"12 Dec 2021"
  },
  {
      id:2,
      icon:"ri-file-pdf-fill",
      iconBackgroundClass:"danger",
      fileName:"Bank Management System",
      fileType:"PDF File",
      fileSize:"8.89 MB",
      updatedDate:"24 Nov 2021"
  },
]


export { projectList, document };
