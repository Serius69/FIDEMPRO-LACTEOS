const todoList = [
  {
      id: "1",
      task: "Added Select2",
      subItem: [
          'assets/images/users/avatar-1.jpg',
          'assets/images/users/avatar-3.jpg'
      ],
      dueDate: "25 Jan, 2022",
      status: "Pending",
      priority: "High"
  },
  {
      id: "2",
      task: "Additional Calendar",
      subItem: [
          'assets/images/users/avatar-5.jpg',
          'assets/images/users/avatar-9.jpg',
          'assets/images/users/avatar-10.jpg'
      ],
      dueDate: "23 Apr, 2022",
      status: "Completed",
      priority: "Medium"
  },
  {
      id: "3",
      task: "Add Dynamic Contact List",
      subItem: [
          'assets/images/users/avatar-5.jpg',
          'assets/images/users/avatar-6.jpg',
          'assets/images/users/avatar-7.jpg',
          'assets/images/users/avatar-8.jpg'
      ],
      dueDate: "24 Apr, 2022",
      status: "Inprogress",
      priority: "Low"
  },
  {
      id: "4",
      task: "Brand Logo design",
      subItem: [
          'assets/images/users/avatar-2.jpg',
          'assets/images/users/avatar-10.jpg',
          'assets/images/users/avatar-9.jpg'
      ],
      dueDate: "25 Apr, 2022",
      status: "New",
      priority: "Medium"
  },
  {
      id: "5",
      task: "Change email option process",
      subItem: [
          'assets/images/users/avatar-3.jpg',
          'assets/images/users/avatar-10.jpg',
          'assets/images/users/avatar-9.jpg'
      ],
      dueDate: "25 Apr, 2022",
      status: "Completed",
      priority: "High"
  },
  {
      id: "6",
      task: "Make a creating an account profile",
      subItem: [
          'assets/images/users/avatar-3.jpg'
      ],
      dueDate: "26 Apr, 2022",
      status: "Completed",
      priority: "Medium"
  },
  {
      id: "7",
      task: "Profile Page Structure",
      subItem: [
          'assets/images/users/avatar-4.jpg',
          'assets/images/users/avatar-5.jpg'
      ],
      dueDate: "27 Apr, 2022",
      status: "New",
      priority: "Low"
  },
  {
      id: "8",
      task: "Datatable with jQuery cdn",
      subItem: [
          'assets/images/users/avatar-6.jpg',
          'assets/images/users/avatar-7.jpg',
          'assets/images/users/avatar-8.jpg'
      ],
      dueDate: "28 Apr, 2022",
      status: "Pending",
      priority: "High"
  },
  {
      id: "9",
      task: "Added File Manager Apps",
      subItem: [
          'assets/images/users/avatar-3.jpg',
          'assets/images/users/avatar-4.jpg',
          'assets/images/users/avatar-5.jpg'
      ],
      dueDate: "29 Apr, 2022",
      status: "Completed",
      priority: "Medium"
  },
  {
      id: "10",
      task: "Added Back to Top button",
      subItem: [
          'assets/images/users/avatar-6.jpg',
          'assets/images/users/avatar-7.jpg'
      ],
      dueDate: "30 Apr, 2022",
      status: "Inprogress",
      priority: "High"
  },
  {
      id: "11",
      task: "Added bdge new style - gradient",
      subItem: [
          'assets/images/users/avatar-3.jpg',
          'assets/images/users/avatar-10.jpg',
          'assets/images/users/avatar-9.jpg'
      ],
      dueDate: "01 May, 2022",
      status: "Inprogress",
      priority: "Medium"
  },
  {
      id: "12",
      task: "Added new tabs styles",
      subItem: [
          'assets/images/users/avatar-2.jpg'
      ],
      dueDate: "01 May, 2022",
      status: "New",
      priority: "Low"
  },
  {
      id: "13",
      task: "Make a creating an account profile",
      subItem: [
          'assets/images/users/avatar-5.jpg',
          'assets/images/users/avatar-6.jpg',
          'assets/images/users/avatar-7.jpg',
          'assets/images/users/avatar-8.jpg'
      ],
      dueDate: "02 May, 2022",
      status: "Completed",
      priority: "Low"
  },
  {
      id: "14",
      task: "Additional Mailbox",
      subItem: [
          'assets/images/users/avatar-5.jpg',
          'assets/images/users/avatar-9.jpg',
          'assets/images/users/avatar-10.jpg'
      ],
      dueDate: "02 Apr, 2022",
      status: "Pending",
      priority: "Medium"
  },
  {
      id: "15",
      task: "Added Email Templates",
      subItem: [
          'assets/images/users/avatar-1.jpg',
          'assets/images/users/avatar-3.jpg'
      ],
      dueDate: "03 Apr, 2022",
      status: "Inprogress",
      priority: "High"
  },
];

const AssignedData = [
  { id: 1, profile: "avatar-1.jpg", name: "Anna Adame" },
  { id: 2, profile: "avatar-2.jpg", name: "Herbert Stokes" },
  { id: 3, profile: "avatar-3.jpg", name: "Frank Hook" },
  { id: 4, profile: "avatar-4.jpg", name: "Mary Gant" },
  { id: 5, profile: "avatar-5.jpg", name: "Nancy Martino" },
  { id: 6, profile: "avatar-6.jpg", name: "Alexis Clarke" },
  { id: 7, profile: "avatar-7.jpg", name: "Michael Morris" },
  { id: 8, profile: "avatar-8.jpg", name: "Thomas Taylor" },
  { id: 9, profile: "avatar-9.jpg", name: "Diego Norris" },
  { id: 10, profile: "avatar-10.jpg", name: "Tonya Noble" },
];

const projectList = [
  {
      id: "1",
      title: "Velzon Admin & Dashboard",
      coll:"velzonAdmin",
      subItem: [
          {
              version: 'v1.4.0',
              color: 'danger'
          },
          {
              version: 'v1.5.0',
              color: 'secondary'
          },
          {
              version: 'v1.6.0',
              color: 'info'
          },
          {
              version: 'v1.7.0',
              color: 'primary'
          },
          {
              version: 'v1.8.0',
              color: 'warning'
          }
      ],
  },
  {
      id: "2",
      title: "Project Management",
      coll:"projectCollapsed",
      subItem: [
          {
              version: 'v2.1.0',
              color: 'danger'
          },
          {
              version: 'v2.2.0',
              color: 'secondary'
          },
          {
              version: 'v2.3.0',
              color: 'info'
          },
          {
              version: 'v2.4.0',
              color: 'primary'
          }
      ],
  },
  {
      id: "3",
      title: "Skote Admin & Dashboard",
      coll:"skoteCollapsed",
      subItem: [
          {
              version: 'v4.1.0',
              color: 'danger'
          },
          {
              version: 'v4.2.0',
              color: 'secondary'
          }
      ],
  },
  {
      id: "4",
      title: "Doot - Chat App Template",
      coll:"ecommerceCollapsed",
      subItem: [
          {
              version: 'v1.0.0',
              color: 'danger'
          },
          {
              version: 'v1.1.0',
              color: 'secondary'
          },
          {
              version: 'v1.2.0',
              color: 'info'
          },
      ],
  },
]

export { todoList, AssignedData, projectList };
