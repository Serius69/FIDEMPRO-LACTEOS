import { MenuItem } from './menu.model';

export const MENU: MenuItem[] = [
  {
    id: 1,
    label: 'MENUITEMS.MENU.TEXT',
    isTitle: true
  },
  {
    id: 2,
    label: 'Home',
    icon: 'ri-dashboard-2-line',
    link: '/home'
  },
  {
    id: 3,
    label: 'Product',
    icon: 'ri-dashboard-2-line',
    subItems: [
      {
        id: 4,
        label: 'Add',
        link: '/create',
        parentId: 3
      },
      {
        id: 5,
        label: 'List',
        link: '/list',
        parentId: 3
      },
    ]
  },
  {
    id: 6,
    label: 'Variable',
    icon: 'ri-dashboard-2-line',
    subItems: [
      {
        id: 7,
        label: 'Add',
        link: '/add',
        parentId: 6
      },
      {
        id: 7,
        label: 'List',
        link: '/listvariable',
        parentId: 6
      },
    ]
  },
  {
    id: 8,
    label: 'Simulation',
    icon: 'ri-dashboard-2-line',
    link: '/simulation'
  },  
  {
    id: 9,
    label: 'Dashboard',
    icon: 'ri-dashboard-2-line',
    subItems: [
      {
        id: 6,
        label: 'CRM',
        link: '/crm',
        parentId: 9
      },
      {
        id: 7,
        label: 'Analitycs',
        link: '/analytics',
        parentId: 9
      },
    ]
  }
];
