const productListWidgets = [
  {
    id: 1,
    time: "Updated 3hrs ago",
    img: 'assets/images/brands/slack.png',
    label: 'Slack brand logo design',
    caption: 'Create a Brand logo design for a velzon admin.',
    number: '18/42',
    progressBar: 34,
    date: '10 Jul, 2021',
    users: [
      {
        name: 'Darline Williams',
        profile: 'assets/images/users/avatar-2.jpg'
      },
      {
        name: 'Add Members',
        text: "+",
        variant: 'bg-light text-primary'
      }
    ],
    isIcon: true
  }
];

const productListWidgets1 = [
  {
    id: 5,
    label: "Multipurpose landing template",
    status: 'Inprogress',
    statusClass: 'warning',
    deadline : '18 Sep, 2021',
    progressBar: 50,
    bg_color: "danger",
    users: [
      {
        name: 'Donna Kline',
        text: 'D',
        variant: 'bg-danger'
      },
      {
        name: 'Lee Winton',
        profile: 'assets/images/users/avatar-5.jpg'
      },
      {
        name: 'Johnny Shorter',
        profile: 'assets/images/users/avatar-6.jpg'
      },
      {
        name: 'Add Members',
        text: "+",
        variant: 'bg-light text-primary'
      }
    ]
  }
];

const productListWidgets2 = [
  {
    id: 9,
    img: "assets/images/brands/dribbble.png",
    label: 'Kanban Board',
    status: 'Inprogress',
    statusClass: 'warning',
    deadline : '08 Dec, 2021',
    number : '17/20',
    progressBar: 71,
    bg_color: "bg-secondary-subtle",
    users: [
      {
        name: 'Terry Moberly',
        text: 'T',
        variant: 'bg-danger'
      },
      {
        name: 'Ruby Miller',
        profile: 'assets/images/users/avatar-5.jpg'
      },
      {
        name: 'Add Members',
        text: "+",
        variant: 'bg-light text-primary'
      }
    ]
  },
];

export { productListWidgets, productListWidgets1, productListWidgets2 };
