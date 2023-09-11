/**
 * Group List
 */
 const groupData = [
    {
        name: 'Landing Design',
        unread: '7'
    },
    {
      name: 'General'
    },
    {
      name: 'Project Tasks',
      unread: '3'
    },
    {
        name: 'Meeting'
    },
    {
        name: 'Reporting'
    },
  ];
  
  /**
   * Chat List
   */
   const chatData = [
    {
        image: 'assets/images/users/avatar-2.jpg',
        name: 'Lisa Parker',
        status: 'online'
    },
    {
        image: 'assets/images/users/avatar-3.jpg',
        name: 'Frank Thomas',
        status: 'online',
        unread: '8'
    },
    {
      name: 'Clifford Taylor',
      status: 'away'
    },
    {
        image: 'assets/images/users/avatar-4.jpg',
        name: 'Janette Caster',
        status: 'online'
    },
    {
        image: 'assets/images/users/avatar-5.jpg',
        name: 'Sarah Beattie',
        status: 'online',
        unread: '5'
    },
    {
        image: 'assets/images/users/avatar-6.jpg',
        name: 'Nellie Cornett',
        status: 'away',
        unread: '2'
    },
    {
        name: 'Chris Kiernan',
        status: 'online'
    },
    {
        name: 'Edith Evans',
        status: 'away'
    },
    {
        image: 'assets/images/users/avatar-7.jpg',
        name: 'Joseph Siegel',
        status: 'away'
    },
  ];
  
  /**
   * Chat Message List
   */
   const chatMessagesData = [
    {
        profile: 'assets/images/users/avatar-2.jpg',
        message: 'Good morning 😊',
        time: '09:07 am'
    },
    {
        align: 'right',
        message: 'Good morning, How are you? What about our next meeting?',
        time: '09:08 am'
    },
    {
        profile: 'assets/images/users/avatar-2.jpg',
        message: `Hey, I'm going to meet a friend of mine at the department store. I have to buy some presents for my parents 🎁.`,
        time: '09:10 am'
    },
    {
        align: 'right',
        message: `Wow that's great`,
        time: '09:12 am'
    },
    {
        profile: 'assets/images/users/avatar-2.jpg',
        time: '09:30 am',
        image: ['assets/images/small/img-1.jpg', 'assets/images/small/img-2.jpg']
    },
    {
        align: 'right',
        replayName: "You",
        replaymsg: `Wow that's great`,
        message: 'Thanks',
        time: '09:08 am'
    },
  ];

  /**
   * Contact List
   */
  const contactData = [
    {
        title: 'A',
        contacts: [
            {
                name: 'Alice Cruickshank',
            }
          ],
    },
    {
        title: 'B',
        contacts: [
            {
                name: 'Barrett Brown',
                profile:'assets/images/users/avatar-4.jpg'
            }
        ],
    },
    {
        title: 'C',
        contacts: [
            {
                name: 'Chris Kiernan',
            },
            {
                name: 'Clifford Taylor',
            }
        ],
    },
    {
        title: 'E',
        contacts: [
            {
                name: 'Edith Evans',
            }
        ],
    },
    {
        title: 'F',
        contacts: [
            {
                name: 'Frank Thomas',
                profile:'assets/images/users/avatar-3.jpg'
            }
        ],
    },
    {
        title: 'G',
        contacts: [
            {
                name: 'Gilbert Beer'
            }
        ],
    },
    {
        title: 'J',
        contacts: [
            {
                name: 'Janette Caster',
                profile:'assets/images/users/avatar-4.jpg'
            },
            {
                name: 'Joseph Siegel',
                profile:'assets/images/users/avatar-7.jpg'
            },
            {
                name: 'Justyn Wisoky',
                profile:'assets/images/users/avatar-1.jpg'
            }
        ],
    },
    {
        title: 'K',
        contacts: [
            {
                name: 'Keaton King',
                profile:'assets/images/users/avatar-5.jpg'
            }
        ],
    },
    {
        title: 'L',
        contacts: [
            {
                name: 'Lisa Parker',
                profile:'assets/images/users/avatar-2.jpg'
            }
        ],
    },
    {
        title: 'M',
        contacts: [
            {
                name: 'Marian Moen'
            }
        ],
    },
    {
        title: 'N',
        contacts: [
            {
                name: 'Nellie Cornett',
                profile:'assets/images/users/avatar-6.jpg'
            }
        ],
    },
    {
        title: 'R',
        contacts: [
            {
                name: 'Ronald Downey'
            }
        ],
    },
    {
        title: 'S',
        contacts: [
            {
                name: 'Sarah Beattie',
                profile:'assets/images/users/avatar-5.jpg'
            }
        ],
    },
    {
        title: 'V',
        contacts: [
            {
                name: 'Victor Beahan',
                profile:'assets/images/users/avatar-10.jpg'
            }
        ],
    },
    {
        title: 'W',
        contacts: [
            {
                name: 'Wayne Runte',
                profile:'assets/images/users/avatar-2.jpg'
            }
        ],
    },
  ];
  
  export { groupData, chatData, chatMessagesData, contactData };
  