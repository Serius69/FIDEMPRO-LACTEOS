import { MenuItem } from './menu.model';

export const MENU: MenuItem[] = [
  {
    id: 1,
    label: 'MENUITEMS.MENU.TEXT',
    isTitle: true
  },
  {
    id: 2,
    label: 'MENUITEMS.DASHBOARD.TEXT',
    collapseid: 'sidebarDashboards',
    icon: 'ri-dashboard-2-line',
    subItems: [
      {
        id: 3,
        label: 'MENUITEMS.DASHBOARD.LIST.ANALYTICS',
        link: '/analytics',
        parentId: 2
      },
      {
        id: 4,
        label: 'MENUITEMS.DASHBOARD.LIST.CRM',
        link: '/crm',
        parentId: 2
      },
      {
        id: 5,
        label: 'MENUITEMS.DASHBOARD.LIST.ECOMMERCE',
        link: '',
        parentId: 2
      },
      {
        id: 6,
        label: 'MENUITEMS.DASHBOARD.LIST.CRYPTO',
        link: '/crypto',
        parentId: 2
      },
      {
        id: 7,
        label: 'MENUITEMS.DASHBOARD.LIST.PROJECTS',
        link: '/projects',
        parentId: 2
      },
      {
        id: 7,
        label: 'MENUITEMS.DASHBOARD.LIST.NFT',
        link: '/nft',
        parentId: 2
      },
      {
        id: 8,
        label: 'MENUITEMS.DASHBOARD.LIST.JOB',
        link: '/job',
        parentId: 2,
      }
    ]
  },
  {
    id: 8,
    label: 'MENUITEMS.APPS.TEXT',
    collapseid: 'sidebarApps',
    icon: 'ri-apps-2-line',
    subItems: [
      {
        id: 9,
        label: 'MENUITEMS.APPS.LIST.CALENDAR',
        link: '/calendar',
        parentId: 8
      },
      {
        id: 10,
        label: 'MENUITEMS.APPS.LIST.CHAT',
        link: '/chat',
        parentId: 8
      },
      {
        id: 11,
        label: 'MENUITEMS.APPS.LIST.EMAIL',
        parentId: 8,
        subItems: [
          {
            id: 13,
            label: 'MENUITEMS.APPS.LIST.MAILBOX',
            link: '/mailbox',
            parentId: 11
          },
          {
            id: 14,
            label: 'MENUITEMS.APPS.LIST.MAILTEMPLATES',
            parentId: 11,
            subItems: [
              {
                id: 13,
                label: 'MENUITEMS.APPS.LIST.BASICACTION',
                link: '/email-basic',
                parentId: 14
              },
              {
                id: 13,
                label: 'MENUITEMS.APPS.LIST.ECOMMERCEACTION',
                link: '/email-ecommerce',
                parentId: 14
              },
            ]
          }
        ]
      },
      {
        id: 12,
        label: 'MENUITEMS.APPS.LIST.ECOMMERCE',
        link: '/mailbox',
        parentId: 8,
        collapseid: 'ecommerce',
        subItems: [
          {
            id: 13,
            label: 'MENUITEMS.APPS.LIST.PRODUCTS',
            link: '/ecommerce/products',
            parentId: 12
          },
          {
            id: 14,
            label: 'MENUITEMS.APPS.LIST.PRODUCTDETAILS',
            link: '/ecommerce/product-detail/1',
            parentId: 12
          },
          {
            id: 15,
            label: 'MENUITEMS.APPS.LIST.CREATEPRODUCT',
            link: '/ecommerce/add-product',
            parentId: 12
          },
          {
            id: 16,
            label: 'MENUITEMS.APPS.LIST.ORDERS',
            link: '/ecommerce/orders',
            parentId: 12
          },
          {
            id: 17,
            label: 'MENUITEMS.APPS.LIST.ORDERDETAILS',
            link: '/ecommerce/order-details',
            parentId: 12
          },
          {
            id: 18,
            label: 'MENUITEMS.APPS.LIST.CUSTOMERS',
            link: '/ecommerce/customers',
            parentId: 12
          },
          {
            id: 19,
            label: 'MENUITEMS.APPS.LIST.SHOPPINGCART',
            link: '/ecommerce/cart',
            parentId: 12
          },
          {
            id: 20,
            label: 'MENUITEMS.APPS.LIST.CHECKOUT',
            link: '/ecommerce/checkout',
            parentId: 12
          },
          {
            id: 21,
            label: 'MENUITEMS.APPS.LIST.SELLERS',
            link: '/ecommerce/sellers',
            parentId: 12
          },
          {
            id: 22,
            label: 'MENUITEMS.APPS.LIST.SELLERDETAILS',
            link: '/ecommerce/seller-details',
            parentId: 12
          }
        ]
      },
      {
        id: 23,
        label: 'MENUITEMS.APPS.LIST.PROJECTS',
        parentId: 8,
        subItems: [
          {
            id: 24,
            label: 'MENUITEMS.APPS.LIST.LIST',
            link: '/projects/list',
            parentId: 23
          },
          {
            id: 25,
            label: 'MENUITEMS.APPS.LIST.OVERVIEW',
            link: '/projects/overview',
            parentId: 23
          },
          {
            id: 26,
            label: 'MENUITEMS.APPS.LIST.CREATEPROJECT',
            link: '/projects/create',
            parentId: 23
          }
        ]
      },
      {
        id: 27,
        label: 'MENUITEMS.APPS.LIST.TASK',
        parentId: 8,
        subItems: [
          {
            id: 28,
            label: 'MENUITEMS.APPS.LIST.KANBANBOARD',
            link: '/tasks/kanban',
            parentId: 27
          },
          {
            id: 29,
            label: 'MENUITEMS.APPS.LIST.LISTVIEW',
            link: '/tasks/list-view',
            parentId: 27
          },
          {
            id: 30,
            label: 'MENUITEMS.APPS.LIST.TASKDETAILS',
            link: '/tasks/details',
            parentId: 27
          }
        ]
      },
      {
        id: 31,
        label: 'MENUITEMS.APPS.LIST.CRM',
        parentId: 8,
        subItems: [
          {
            id: 32,
            label: 'MENUITEMS.APPS.LIST.CONTACTS',
            link: '/crm/contacts',
            parentId: 31
          },
          {
            id: 33,
            label: 'MENUITEMS.APPS.LIST.COMPANIES',
            link: '/crm/companies',
            parentId: 31
          },
          {
            id: 34,
            label: 'MENUITEMS.APPS.LIST.DEALS',
            link: '/crm/deals',
            parentId: 31
          },
          {
            id: 35,
            label: 'MENUITEMS.APPS.LIST.LEADS',
            link: '/crm/leads',
            parentId: 31
          }
        ]
      },
      {
        id: 36,
        label: 'MENUITEMS.APPS.LIST.CRYPTO',
        parentId: 8,
        subItems: [
          {
            id: 37,
            label: 'MENUITEMS.APPS.LIST.TRANSACTIONS',
            link: '/crypto/transactions',
            parentId: 36
          },
          {
            id: 38,
            label: 'MENUITEMS.APPS.LIST.BUY&SELL',
            link: '/crypto/buy-sell',
            parentId: 36
          },
          {
            id: 38,
            label: 'MENUITEMS.APPS.LIST.ORDERS',
            link: '/crypto/orders',
            parentId: 36
          },
          {
            id: 39,
            label: 'MENUITEMS.APPS.LIST.MYWALLET',
            link: '/crypto/wallet',
            parentId: 36
          },
          {
            id: 40,
            label: 'MENUITEMS.APPS.LIST.ICOLIST',
            link: '/crypto/ico',
            parentId: 36
          },
          {
            id: 41,
            label: 'MENUITEMS.APPS.LIST.KYCAPPLICATION',
            link: '/crypto/kyc',
            parentId: 36
          }
        ]
      },
      {
        id: 42,
        label: 'MENUITEMS.APPS.LIST.INVOICES',
        parentId: 8,
        subItems: [
          {
            id: 43,
            label: 'MENUITEMS.APPS.LIST.LISTVIEW',
            link: '/invoices/list',
            parentId: 42
          },
          {
            id: 44,
            label: 'MENUITEMS.APPS.LIST.DETAILS',
            link: '/invoices/details',
            parentId: 42
          },
          {
            id: 45,
            label: 'MENUITEMS.APPS.LIST.CREATEINVOICE',
            link: '/invoices/create',
            parentId: 42
          }
        ]
      },
      {
        id: 46,
        label: 'MENUITEMS.APPS.LIST.SUPPORTTICKETS',
        parentId: 8,
        subItems: [
          {
            id: 47,
            label: 'MENUITEMS.APPS.LIST.LISTVIEW',
            link: '/tickets/list',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.TICKETDETAILS',
            link: '/tickets/details',
            parentId: 46
          }
        ]
      },
      {
        id: 46,
        label: 'MENUITEMS.APPS.LIST.NFTMARKETPLACE',
        parentId: 8,
        subItems: [
          {
            id: 47,
            label: 'MENUITEMS.APPS.LIST.MARKETPLACE',
            link: '/marletplace/marketplace',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.EXPLORENOW',
            link: '/marletplace/explore',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.LIVEAUCTION',
            link: '/marletplace/auction',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.ITEMDETAILS',
            link: '/marletplace/item-details',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.COLLECTIONS',
            link: '/marletplace/collections',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.CREATORS',
            link: '/marletplace/creators',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.RANKING',
            link: '/marletplace/raking',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.WALLETCONNECT',
            link: '/marletplace/wallet',
            parentId: 46
          },
          {
            id: 48,
            label: 'MENUITEMS.APPS.LIST.CREATENFT',
            link: '/marletplace/create',
            parentId: 46
          },
        ]
      },
      {
        id: 49,
        label: 'MENUITEMS.APPS.LIST.FILEMANAGER',
        link: '/file-manager',
        parentId: 8,
      },
      {
        id: 50,
        label: 'MENUITEMS.APPS.LIST.TODO',
        link: '/todo',
        parentId: 8,
      },
      {
        id: 51,
        label: 'MENUITEMS.APPS.LIST.JOBS',
        parentId: 8,
        subItems: [
          {
            id: 52,
            label: 'MENUITEMS.APPS.LIST.STATISTICS',
            link: '/jobs/statistics',
            parentId: 51
          },
          {
            id: 53,
            label: 'MENUITEMS.APPS.LIST.JOBLISTS',
            subItems: [
              {
                id: 54,
                label: 'MENUITEMS.APPS.LIST.LIST',
                link: '/jobs/list',
                parentId: 53
              },
              {
                id: 55,
                label: 'MENUITEMS.APPS.LIST.GRID',
                link: '/jobs/grid',
                parentId: 53
              },
              {
                id: 56,
                label: 'MENUITEMS.APPS.LIST.OVERVIEW',
                link: '/jobs/overview',
                parentId: 53
              }
            ]
          },
          {
            id: 57,
            label: 'MENUITEMS.APPS.LIST.CANDIDATELISTS',
            subItems: [
              {
                id: 58,
                label: 'MENUITEMS.APPS.LIST.LISTVIEW',
                link: '/jobs/listview',
                parentId: 57
              },
              {
                id: 59,
                label: 'MENUITEMS.APPS.LIST.GRIDVIEW',
                link: '/jobs/gridview',
                parentId: 57
              }
            ]
          },
          {
            id: 60,
            label: 'MENUITEMS.APPS.LIST.APPLICATION',
            link: '/jobs/application',
            parentId: 51
          },
          {
            id: 61,
            label: 'MENUITEMS.APPS.LIST.NEWJOB',
            link: '/jobs/newjob',
            parentId: 51
          },
          {
            id: 62,
            label: 'MENUITEMS.APPS.LIST.COMPANIESLIST',
            link: '/jobs/companies-list',
            parentId: 51
          },
          {
            id: 63,
            label: 'MENUITEMS.APPS.LIST.JOBCATEGORIES',
            link: '/jobs/job-categories',
            parentId: 51
          },
        ]
      },
      {
        id: 64,
        label: 'MENUITEMS.APPS.LIST.APIKEY',
        link: '/apikey',
        parentId: 8,
      },
    ]
  },
  {
    id: 54,
    label: 'MENUITEMS.PAGES.TEXT',
    isTitle: true
  },
  {
    id: 55,
    label: 'MENUITEMS.AUTHENTICATION.TEXT',
    collapseid: 'sidebarAuth',
    icon: 'ri-account-circle-line',
    subItems: [
      {
        id: 56,
        label: 'MENUITEMS.AUTHENTICATION.LIST.SIGNIN',
        parentId: 49,
        subItems: [
          {
            id: 57,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/signin/basic',
            parentId: 56
          },
          {
            id: 58,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/signin/cover',
            parentId: 56
          },
        ]
      },
      {
        id: 59,
        label: 'MENUITEMS.AUTHENTICATION.LIST.SIGNUP',
        parentId: 49,
        subItems: [
          {
            id: 60,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/signup/basic',
            parentId: 59
          },
          {
            id: 61,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/signup/cover',
            parentId: 59
          },
        ]
      },
      {
        id: 62,
        label: 'MENUITEMS.AUTHENTICATION.LIST.PASSWORDRESET',
        parentId: 49,
        subItems: [
          {
            id: 63,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/pass-reset/basic',
            parentId: 62
          },
          {
            id: 64,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/pass-reset/cover',
            parentId: 62
          },
        ]
      },
      {
        id: 62,
        label: 'MENUITEMS.AUTHENTICATION.LIST.PASSWORDCREATE',
        parentId: 49,
        subItems: [
          {
            id: 63,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/pass-create/basic',
            parentId: 62
          },
          {
            id: 64,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/pass-create/cover',
            parentId: 62
          },
        ]
      },
      {
        id: 65,
        label: 'MENUITEMS.AUTHENTICATION.LIST.LOCKSCREEN',
        parentId: 49,
        subItems: [
          {
            id: 66,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/lockscreen/basic',
            parentId: 65
          },
          {
            id: 67,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/lockscreen/cover',
            parentId: 65
          },
        ]
      },
      {
        id: 68,
        label: 'MENUITEMS.AUTHENTICATION.LIST.LOGOUT',
        parentId: 49,
        subItems: [
          {
            id: 69,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/logout/basic',
            parentId: 68
          },
          {
            id: 70,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/logout/cover',
            parentId: 68
          },
        ]
      },
      {
        id: 71,
        label: 'MENUITEMS.AUTHENTICATION.LIST.SUCCESSMESSAGE',
        parentId: 49,
        subItems: [
          {
            id: 72,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/success-msg/basic',
            parentId: 71
          },
          {
            id: 73,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/success-msg/cover',
            parentId: 71
          },
        ]
      },
      {
        id: 74,
        label: 'MENUITEMS.AUTHENTICATION.LIST.TWOSTEPVERIFICATION',
        parentId: 49,
        subItems: [
          {
            id: 75,
            label: 'MENUITEMS.AUTHENTICATION.LIST.BASIC',
            link: '/auth/twostep/basic',
            parentId: 74
          },
          {
            id: 76,
            label: 'MENUITEMS.AUTHENTICATION.LIST.COVER',
            link: '/auth/twostep/cover',
            parentId: 74
          },
        ]
      },
      {
        id: 77,
        label: 'MENUITEMS.AUTHENTICATION.LIST.ERRORS',
        parentId: 49,
        subItems: [
          {
            id: 78,
            label: 'MENUITEMS.AUTHENTICATION.LIST.404BASIC',
            link: '/auth/errors/404-basic',
            parentId: 77
          },
          {
            id: 79,
            label: 'MENUITEMS.AUTHENTICATION.LIST.404COVER',
            link: '/auth/errors/404-cover',
            parentId: 77
          },
          {
            id: 80,
            label: 'MENUITEMS.AUTHENTICATION.LIST.404ALT',
            link: '/auth/errors/404-alt',
            parentId: 77
          },
          {
            id: 81,
            label: 'MENUITEMS.AUTHENTICATION.LIST.500',
            link: '/auth/errors/page-500',
            parentId: 77
          },
          {
            id: 81,
            label: 'MENUITEMS.AUTHENTICATION.LIST.OFFLINE',
            link: '/auth/errors/offline',
            parentId: 77
          },
        ]
      },
    ]
  },
  {
    id: 82,
    label: 'MENUITEMS.PAGES.TEXT',
    icon: 'ri-pages-line',
    collapseid: 'sidebarPages',
    subItems: [
      {
        id: 83,
        label: 'MENUITEMS.PAGES.LIST.STARTER',
        link: '/pages/starter',
        parentId: 82
      },
      {
        id: 84,
        label: 'MENUITEMS.PAGES.LIST.PROFILE',
        parentId: 82,
        subItems: [
          {
            id: 85,
            label: 'MENUITEMS.PAGES.LIST.SIMPLEPAGE',
            link: '/pages/profile',
            parentId: 84
          },
          {
            id: 86,
            label: 'MENUITEMS.PAGES.LIST.SETTINGS',
            link: '/pages/profile-setting',
            parentId: 84
          },
        ]
      },
      {
        id: 87,
        label: 'MENUITEMS.PAGES.LIST.TEAM',
        link: '/pages/team',
        parentId: 82
      },
      {
        id: 88,
        label: 'MENUITEMS.PAGES.LIST.TIMELINE',
        link: '/pages/timeline',
        parentId: 82
      },
      {
        id: 89,
        label: 'MENUITEMS.PAGES.LIST.FAQS',
        link: '/pages/faqs',
        parentId: 82
      },
      {
        id: 90,
        label: 'MENUITEMS.PAGES.LIST.PRICING',
        link: '/pages/pricing',
        parentId: 82
      },
      {
        id: 91,
        label: 'MENUITEMS.PAGES.LIST.GALLERY',
        link: '/pages/gallery',
        parentId: 82
      },
      {
        id: 92,
        label: 'MENUITEMS.PAGES.LIST.MAINTENANCE',
        link: '/pages/maintenance',
        parentId: 82
      },
      {
        id: 93,
        label: 'MENUITEMS.PAGES.LIST.COMINGSOON',
        link: '/pages/coming-soon',
        parentId: 82
      },
      {
        id: 94,
        label: 'MENUITEMS.PAGES.LIST.SITEMAP',
        link: '/pages/sitemap',
        parentId: 82
      },
      {
        id: 95,
        label: 'MENUITEMS.PAGES.LIST.SEARCHRESULTS',
        link: '/pages/search-results',
        parentId: 82
      },
      {
        id: 96,
        label: 'MENUITEMS.PAGES.LIST.PRIVACYPOLICY',
        link: '/pages/privacy-policy',
        parentId: 82
      },
      {
        id: 97,
        label: 'MENUITEMS.PAGES.LIST.TERMS&CONDITIONS',
        link: '/pages/terms-condition',
        parentId: 82
      }
    ]
  },
  {
    id: 97,
    label: 'MENUITEMS.LANDING.TEXT',
    collapseid: 'sidebarUI',
    icon: 'ri-rocket-line',
    subItems: [
      {
        id: 85,
        label: 'MENUITEMS.LANDING.LIST.ONEPAGE',
        link: '/landing',
        parentId: 84
      },
      {
        id: 86,
        label: 'MENUITEMS.LANDING.LIST.NFTLANDING',
        link: '/landing/nft',
        parentId: 84
      },
      {
        id: 87,
        label: 'MENUITEMS.LANDING.LIST.JOB',
        link: '/landing/job',
        parentId: 84,
      },
    ]
  },
  {
    id: 96,
    label: 'MENUITEMS.COMPONENTS.TEXT',
    isTitle: true
  },
  {
    id: 97,
    label: 'MENUITEMS.BASEUI.TEXT',
    collapseid: 'sidebarBasicUI',
    icon: 'ri-pencil-ruler-2-line',
    subItems: [
      {
        id: 98,
        label: 'MENUITEMS.BASEUI.LIST.ALERTS',
        link: '/ui/alerts',
        parentId: 97
      },
      {
        id: 99,
        label: 'MENUITEMS.BASEUI.LIST.BADGES',
        link: '/ui/badges',
        parentId: 97
      },
      {
        id: 100,
        label: 'MENUITEMS.BASEUI.LIST.BUTTONS',
        link: '/ui/buttons',
        parentId: 97
      },
      {
        id: 101,
        label: 'MENUITEMS.BASEUI.LIST.COLORS',
        link: '/ui/colors',
        parentId: 97
      },
      {
        id: 102,
        label: 'MENUITEMS.BASEUI.LIST.CARDS',
        link: '/ui/cards',
        parentId: 97
      },
      {
        id: 103,
        label: 'MENUITEMS.BASEUI.LIST.CAROUSEL',
        link: '/ui/carousel',
        parentId: 97
      },
      {
        id: 104,
        label: 'MENUITEMS.BASEUI.LIST.DROPDOWNS',
        link: '/ui/dropdowns',
        parentId: 97
      },
      {
        id: 105,
        label: 'MENUITEMS.BASEUI.LIST.GRID',
        link: '/ui/grid',
        parentId: 97
      },
      {
        id: 106,
        label: 'MENUITEMS.BASEUI.LIST.IMAGES',
        link: '/ui/images',
        parentId: 97
      },
      {
        id: 107,
        label: 'MENUITEMS.BASEUI.LIST.TABS',
        link: '/ui/tabs',
        parentId: 97
      },
      {
        id: 108,
        label: 'MENUITEMS.BASEUI.LIST.ACCORDION&COLLAPSE',
        link: '/ui/accordions',
        parentId: 97
      },
      {
        id: 109,
        label: 'MENUITEMS.BASEUI.LIST.MODALS',
        link: '/ui/modals',
        parentId: 97
      },
      {
        id: 111,
        label: 'MENUITEMS.BASEUI.LIST.PLACEHOLDERS',
        link: '/ui/placeholder',
        parentId: 97
      },
      {
        id: 112,
        label: 'MENUITEMS.BASEUI.LIST.PROGRESS',
        link: '/ui/progress',
        parentId: 97
      },
      {
        id: 113,
        label: 'MENUITEMS.BASEUI.LIST.NOTIFICATIONS',
        link: '/ui/notifications',
        parentId: 97
      },
      {
        id: 114,
        label: 'MENUITEMS.BASEUI.LIST.MEDIAOBJECT',
        link: '/ui/media',
        parentId: 97
      },
      {
        id: 115,
        label: 'MENUITEMS.BASEUI.LIST.EMBEDVIDEO',
        link: '/ui/video',
        parentId: 97
      },
      {
        id: 116,
        label: 'MENUITEMS.BASEUI.LIST.TYPOGRAPHY',
        link: '/ui/typography',
        parentId: 97
      },
      {
        id: 117,
        label: 'MENUITEMS.BASEUI.LIST.LISTS',
        link: '/ui/list',
        parentId: 97
      },
      {
        id: 117,
        label: 'MENUITEMS.BASEUI.LIST.LINKS',
        link: '/ui/links',
        badge: {
          variant: 'bg-success',
          text: 'MENUITEMS.DASHBOARD.BADGE',
        },
        parentId: 97
      },
      {
        id: 118,
        label: 'MENUITEMS.BASEUI.LIST.GENERAL',
        link: '/ui/general',
        parentId: 97
      },
      {
        id: 119,
        label: 'MENUITEMS.BASEUI.LIST.RIBBONS',
        link: '/ui/ribbons',
        parentId: 97
      },
      {
        id: 120,
        label: 'MENUITEMS.BASEUI.LIST.UTILITIES',
        link: '/ui/utilities',
        parentId: 97
      }
    ]
  },
  {
    id: 121,
    label: 'MENUITEMS.ADVANCEUI.TEXT',
    icon: 'ri-stack-line',
    collapseid: 'sidebarAdvanceUI',
    badge: {
      variant: 'bg-success',
      text: 'MENUITEMS.ADVANCEUI.BADGE',
    },
    subItems: [
      {
        id: 122,
        label: 'MENUITEMS.ADVANCEUI.LIST.SWEETALERTS',
        link: '/advance-ui/sweetalerts',
        parentId: 121
      },
      {
        id: 124,
        label: 'MENUITEMS.ADVANCEUI.LIST.SCROLLBAR',
        link: '/advance-ui/scrollbar',
        parentId: 121
      },
      {
        id: 126,
        label: 'MENUITEMS.ADVANCEUI.LIST.TOUR',
        link: '/advance-ui/tour',
        parentId: 121
      },
      {
        id: 127,
        label: 'MENUITEMS.ADVANCEUI.LIST.SWIPERSLIDER',
        link: '/advance-ui/swiper',
        parentId: 121
      },
      {
        id: 128,
        label: 'MENUITEMS.ADVANCEUI.LIST.RATTINGS',
        link: '/advance-ui/ratings',
        parentId: 121
      },
      {
        id: 129,
        label: 'MENUITEMS.ADVANCEUI.LIST.HIGHLIGHT',
        link: '/advance-ui/highlight',
        parentId: 121
      },
      {
        id: 130,
        label: 'MENUITEMS.ADVANCEUI.LIST.SCROLLSPY',
        link: '/advance-ui/scrollspy',
        parentId: 121
      }
    ]
  },
  {
    id: 131,
    label: 'MENUITEMS.WIDGETS.TEXT',
    icon: 'ri-honour-line',
    link: '/widgets'
  },
  {
    id: 132,
    label: 'MENUITEMS.FORMS.TEXT',
    icon: 'ri-file-list-3-line',
    collapseid: 'sidebarForms',
    subItems: [
      {
        id: 133,
        label: 'MENUITEMS.FORMS.LIST.BASICELEMENTS',
        link: '/forms/basic',
        parentId: 132
      },
      {
        id: 134,
        label: 'MENUITEMS.FORMS.LIST.FORMSELECT',
        link: '/forms/select',
        parentId: 132
      },
      {
        id: 135,
        label: 'MENUITEMS.FORMS.LIST.CHECKBOXS&RADIOS',
        link: '/forms/checkboxs-radios',
        parentId: 132
      },
      {
        id: 136,
        label: 'MENUITEMS.FORMS.LIST.PICKERS',
        link: '/forms/pickers',
        parentId: 132
      },
      {
        id: 137,
        label: 'MENUITEMS.FORMS.LIST.INPUTMASKS',
        link: '/forms/masks',
        parentId: 132
      },
      {
        id: 138,
        label: 'MENUITEMS.FORMS.LIST.ADVANCED',
        link: '/forms/advanced',
        parentId: 132
      },
      {
        id: 139,
        label: 'MENUITEMS.FORMS.LIST.RANGESLIDER',
        link: '/forms/range-sliders',
        parentId: 132
      },
      {
        id: 140,
        label: 'MENUITEMS.FORMS.LIST.VALIDATION',
        link: '/forms/validation',
        parentId: 132
      },
      {
        id: 141,
        label: 'MENUITEMS.FORMS.LIST.WIZARD',
        link: '/forms/wizard',
        parentId: 132
      },
      {
        id: 142,
        label: 'MENUITEMS.FORMS.LIST.EDITORS',
        link: '/forms/editors',
        parentId: 132
      },
      {
        id: 143,
        label: 'MENUITEMS.FORMS.LIST.FILEUPLOADS',
        link: '/forms/file-uploads',
        parentId: 132
      },
      {
        id: 144,
        label: 'MENUITEMS.FORMS.LIST.FORMLAYOUTS',
        link: '/forms/layouts',
        parentId: 132
      }
    ]
  },
  {
    id: 145,
    label: 'MENUITEMS.TABLES.TEXT',
    collapseid: 'sidebarTables',
    icon: 'ri-layout-grid-line',
    subItems: [
      {
        id: 146,
        label: 'MENUITEMS.TABLES.LIST.BASICTABLES',
        link: '/tables/basic',
        parentId: 145
      },
      {
        id: 147,
        label: 'MENUITEMS.TABLES.LIST.GRIDJS',
        link: '/tables/gridjs',
        parentId: 145
      },
      {
        id: 148,
        label: 'MENUITEMS.TABLES.LIST.LISTJS',
        link: '/tables/listjs',
        parentId: 145
      }
    ]
  },
  {
    id: 149,
    label: 'MENUITEMS.CHARTS.TEXT',
    collapseid: 'sidebarCharts',
    icon: 'ri-pie-chart-line',
    subItems: [
      {
        id: 150,
        label: 'MENUITEMS.CHARTS.LIST.APEXCHARTS',
        parentId: 149,
        subItems: [
          {
            id: 151,
            label: 'MENUITEMS.CHARTS.LIST.LINE',
            link: '/charts/apex-line',
            parentId: 150
          },
          {
            id: 152,
            label: 'MENUITEMS.CHARTS.LIST.AREA',
            link: '/charts/apex-area',
            parentId: 150
          },
          {
            id: 153,
            label: 'MENUITEMS.CHARTS.LIST.COLUMN',
            link: '/charts/apex-column',
            parentId: 150
          },
          {
            id: 154,
            label: 'MENUITEMS.CHARTS.LIST.BAR',
            link: '/charts/apex-bar',
            parentId: 150
          },
          {
            id: 155,
            label: 'MENUITEMS.CHARTS.LIST.MIXED',
            link: '/charts/apex-mixed',
            parentId: 150
          },
          {
            id: 156,
            label: 'MENUITEMS.CHARTS.LIST.TIMELINE',
            link: '/charts/apex-timeline',
            parentId: 150
          },
          {
            id: 157,
            label: 'MENUITEMS.CHARTS.LIST.RANGEAREA',
            link: '/charts/range-area',
            badge: {
              variant: 'bg-success',
              text: 'MENUITEMS.DASHBOARD.BADGE',
            },
            parentId: 150
          },
          {
            id: 157,
            label: 'MENUITEMS.CHARTS.LIST.FUNNEL',
            link: '/charts/funnel',
            badge: {
              variant: 'bg-success',
              text: 'MENUITEMS.DASHBOARD.BADGE',
            },
            parentId: 150
          },
          {
            id: 157,
            label: 'MENUITEMS.CHARTS.LIST.CANDLSTICK',
            link: '/charts/apex-candlestick',
            parentId: 150
          },
          {
            id: 158,
            label: 'MENUITEMS.CHARTS.LIST.BOXPLOT',
            link: '/charts/apex-boxplot',
            parentId: 150
          },
          {
            id: 159,
            label: 'MENUITEMS.CHARTS.LIST.BUBBLE',
            link: '/charts/apex-bubble',
            parentId: 150
          },
          {
            id: 160,
            label: 'MENUITEMS.CHARTS.LIST.SCATTER',
            link: '/charts/apex-scatter',
            parentId: 150
          },
          {
            id: 161,
            label: 'MENUITEMS.CHARTS.LIST.HEATMAP',
            link: '/charts/apex-heatmap',
            parentId: 150
          },
          {
            id: 162,
            label: 'MENUITEMS.CHARTS.LIST.TREEMAP',
            link: '/charts/apex-treemap',
            parentId: 150
          },
          {
            id: 163,
            label: 'MENUITEMS.CHARTS.LIST.PIE',
            link: '/charts/apex-pie',
            parentId: 150
          },
          {
            id: 164,
            label: 'MENUITEMS.CHARTS.LIST.RADIALBAR',
            link: '/charts/apex-radialbar',
            parentId: 150
          },
          {
            id: 165,
            label: 'MENUITEMS.CHARTS.LIST.RADAR',
            link: '/charts/apex-radar',
            parentId: 150
          },
          {
            id: 166,
            label: 'MENUITEMS.CHARTS.LIST.POLARAREA',
            link: '/charts/apex-polar',
            parentId: 150
          },
        ]
      },
      {
        id: 167,
        label: 'MENUITEMS.CHARTS.LIST.CHARTJS',
        link: '/charts/chartjs',
        parentId: 149
      },
      {
        id: 168,
        label: 'MENUITEMS.CHARTS.LIST.ECHARTS',
        link: '/charts/echarts',
        parentId: 149
      }
    ]
  },
  {
    id: 169,
    label: 'MENUITEMS.ICONS.TEXT',
    icon: 'ri-compasses-2-line',
    collapseid: 'sidebarIcons',
    subItems: [
      {
        id: 170,
        label: 'MENUITEMS.ICONS.LIST.REMIX',
        link: '/icons/remix',
        parentId: 169
      },
      {
        id: 171,
        label: 'MENUITEMS.ICONS.LIST.BOXICONS',
        link: '/icons/boxicons',
        parentId: 169
      },
      {
        id: 172,
        label: 'MENUITEMS.ICONS.LIST.MATERIALDESIGN',
        link: '/icons/materialdesign',
        parentId: 169
      },
      {
        id: 173,
        label: 'MENUITEMS.ICONS.LIST.LINEAWESOME',
        link: '/icons/lineawesome',
        parentId: 169
      },
      {
        id: 174,
        label: 'MENUITEMS.ICONS.LIST.FEATHER',
        link: '/icons/feather',
        parentId: 169
      },
      {
        id: 174,
        label: 'MENUITEMS.ICONS.LIST.CRYPTOSVG',
        link: '/icons/icons-crypto',
        parentId: 169,
      },
    ]
  },
  {
    id: 175,
    label: 'MENUITEMS.MAPS.TEXT',
    icon: 'ri-map-pin-line',
    collapseid: 'sidebarMaps',
    subItems: [
      {
        id: 176,
        label: 'MENUITEMS.MAPS.LIST.GOOGLE',
        link: '/maps/google',
        parentId: 175
      },
      {
        id: 178,
        label: 'MENUITEMS.MAPS.LIST.LEAFLET',
        link: '/maps/leaflet',
        parentId: 175
      }
    ]
  },
  {
    id: 179,
    label: 'MENUITEMS.MULTILEVEL.TEXT',
    icon: 'ri-share-line',
    collapseid: 'sidebarMultilevel',
    subItems: [
      {
        id: 180,
        label: 'MENUITEMS.MULTILEVEL.LIST.LEVEL1.1',
        parentId: 179
      },
      {
        id: 181,
        label: 'MENUITEMS.MULTILEVEL.LIST.LEVEL1.2',
        subItems: [
          {
            id: 182,
            label: 'MENUITEMS.MULTILEVEL.LIST.LEVEL1.LEVEL2.1',
            parentId: 181,
          },
          {
            id: 183,
            label: 'MENUITEMS.MULTILEVEL.LIST.LEVEL1.LEVEL2.2',
            parentId: 181,
          }
        ]
      },
    ]
  }

];
