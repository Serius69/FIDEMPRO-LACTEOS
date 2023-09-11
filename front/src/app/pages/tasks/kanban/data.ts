const tasks  = [
  {
      id: '#VL2436',
      title: 'Profile Page Structure',
      date: '03 Jan, 2022',
      content: 'Profile Page means a web page accessible to the public or to guests.',
      progress: 15,
      roles: ['Admin'],
      users: [
        {
          name: 'Alexis',
          profile: 'assets/images/users/avatar-6.jpg'
        },
        {
          name: 'Nancy',
          profile: 'assets/images/users/avatar-5.jpg'
        },
      ],
      view: '04',
      comment: '19',
      pin: '02',
      status: 'Unassigned',
      variant: 'danger'
  },
  {
    id: '#VL2436',
    title: 'Velzon - Admin Layout Design',
    date: '07 Jan, 2022',
    content: 'The dashboard is the front page of the Administration UI.',
    progress: 0,
    roles: ['Layout','Admin','Dashboard'],
    users: [
      {
        name: 'Michael',
        profile: 'assets/images/users/avatar-7.jpg'
      },
      {
        name: 'Alexis',
        profile: 'assets/images/users/avatar-6.jpg'
      },
      {
        name: 'Anna',
        profile: 'assets/images/users/avatar-1.jpg'
      },
    ],
    view: '14',
    comment: '32',
    pin: '05',
    status: 'Unassigned',
    variant: 'primary'
  },
  {
    id: '#VL2436',
    title: 'Admin Layout Design',
    date: '07 Jan, 2022',
    content: 'Landing page template with clean, minimal and modern design.',
    progress: 0,
    roles: ['Design','Website'],
    users: [
      {
        name: 'Tonya',
        profile: 'assets/images/users/avatar-10.jpg'
      },
      {
        name: 'Frank',
        profile: 'assets/images/users/avatar-3.jpg'
      },
      {
        name: 'Herbert',
        profile: 'assets/images/users/avatar-2.jpg'
      },
    ],
    view: '13',
    comment: '52',
    pin: '17',
    status: 'todo',
    variant: 'primary'
  },
  {
    id: '#VL2436',
    title: 'Marketing & Sales',
    date: '27 Dec, 2021',
    content: 'Sales and marketing are two business functions within an organization.',
    progress: 0,
    roles: ['Marketing','Business'],
    users: [
      {
        name: 'Donald',
        profile: 'assets/images/users/avatar-9.jpg'
      },
      {
        name: 'Thomas',
        profile: 'assets/images/users/avatar-8.jpg'
      },
    ],
    view: '24',
    comment: '10',
    pin: '10',
    status: 'todo',
    variant: 'primary'
  },
  {
    id: '#VL2457',
    title: 'Brand Logo Design',
    date: '22 Dec, 2021',
    content: `BrandCrowd's brand logo maker allows you to generate and customize stand-out brand logos in minutes.`,
    progress: 50,
    roles: ['Logo','Design','UI/UX'],
    users: [
      {
        name: 'Nancy',
        profile: 'assets/images/users/avatar-5.jpg'
      },
      {
        name: 'Michael',
        profile: 'assets/images/users/avatar-7.jpg'
      },
      {
        name: 'Alexis',
        profile: 'assets/images/users/avatar-6.jpg'
      },
    ],
    view: '24',
    comment: '10',
    pin: '10',
    status: 'inprogress',
    variant: 'warning'
  },
  {
    id: '#VL2743',
    title: 'Change Old App Icon',
    date: '24 Oct, 2021',
    content: `Change app icons on Android: How do you change the look of your apps.`,
    progress: '',
    roles: ['Design','Website'],
    users: [
      {
        name: 'Tonya',
        profile: 'assets/images/users/avatar-10.jpg'
      },
      {
        name: 'Donald',
        profile: 'assets/images/users/avatar-9.jpg'
      },
      {
        name: 'Nancy',
        profile: 'assets/images/users/avatar-5.jpg'
      },
    ],
    view: '64',
    comment: '35',
    pin: '23',
    status: 'inprogress',
    variant: 'primary'
  },
  {
    id: '#VL2453',
    title: 'Create Product Animations',
    image: 'assets/images/small/img-7.jpg',
    date: '16 Nov, 2021',
    content: `Change app icons on Android: How do you change the look of your apps.`,
    progress: 100,
    roles: ['Ecommerce'],
    users: [
      {
        name: 'Anna',
        profile: 'assets/images/users/avatar-1.jpg'
      },
    ],
    view: '08',
    comment: '54',
    pin: '28',
    status: 'reviews',
    variant: 'success'
  },
  {
    id: '#VL2340',
    title: 'Product Features Analysis',
    date: '05 Jan, 2022',
    content: `An essential part of strategic planning is running a product feature analysis.`,
    progress: 80,
    roles: ['Product','Analysis'],
    users: [
      {
        name: 'Nancy',
        profile: 'assets/images/users/avatar-5.jpg'
      },
      {
        name: 'Alexis',
        profile: 'assets/images/users/avatar-6.jpg'
      },
    ],
    view: '14',
    comment: '31',
    pin: '07',
    status: 'reviews',
    variant: 'warning'
  },
  {
    id: '#VL2462',
    title: 'Create a Graph of Sketch',
    date: '05 Nov, 2021',
    content: `To make a pie chart with equal slices create a perfect circle by selecting an Oval Tool.`,
    progress: '',
    roles: ['Sketch','Marketing','Design'],
    users: [
      {
        name: 'Alexis',
        profile: 'assets/images/users/avatar-4.jpg'
      },
      {
        name: 'Thomas',
        profile: 'assets/images/users/avatar-8.jpg'
      },
      {
        name: 'Herbert',
        profile: 'assets/images/users/avatar-2.jpg'
      },
      {
        name: 'Anna',
        profile: 'assets/images/users/avatar-1.jpg'
      },
    ],
    view: '12',
    comment: '74',
    pin: '37',
    status: 'reviews',
    variant: 'primary'
  },
  {
    id: '#VL2451',
    title: 'Create a Blog Template UI',
    date: '05 Nov, 2021',
    content: `Landing page template with clean, minimal and modern design.`,
    progress: 35,
    roles: ['Design','Website'],
    users: [
      {
        name: 'Nancy',
        profile: 'assets/images/users/avatar-8.jpg'
      },
      {
        name: 'Frank',
        profile: 'assets/images/users/avatar-7.jpg'
      },
      {
        name: 'Tonya',
        profile: 'assets/images/users/avatar-6.jpg'
      }
    ],
    view: '24',
    comment: '10',
    pin: '10',
    status: 'completed',
    variant: 'danger'
  },
  {
    id: '#VL5287',
    title: 'Banner Design for FB & Twitter',
    image: 'assets/images/small/img-4.jpg',
    date: '07 Jan, 2022',
    content: `Landing page template with clean, minimal and modern design.`,
    progress: 0,
    roles: ['UI/UX','Graphic'],
    users: [
      {
        name: 'Frank',
        profile: 'assets/images/users/avatar-3.jpg'
      },
      {
        name: 'Herbert',
        profile: 'assets/images/users/avatar-2.jpg'
      }
    ],
    view: '11',
    comment: '26',
    pin: '30',
    status: 'new',
    variant: 'primary'
  },

];

export { tasks };
