/**
 * Stat Counder Data
 */
const statData = [{
    title: 'CAMPAIGN SENT',
    value: 197,
    icon: 'ri-space-ship-line',
    profit: 'up',

}, {
    title: 'ANNUAL PROFIT',
    value: 489.4,
    icon: 'ri-exchange-dollar-line',
    profit: 'up',
    sign: '$',
    percentage: 'k'

}, {
    title: 'LEAD Conversation',
    value: 32.89,
    icon: 'ri-pulse-line',
    profit: 'down',
    percentage: '%'
}, {
    title: 'DAILY AVERAGE INCOME',
    value: 1596.5,
    icon: 'ri-trophy-line',
    profit: 'up',
    sign: '$'
}, {
    title: 'ANNUAL DEALS',
    value: 2659,
    icon: 'ri-service-line',
    profit: 'down',

}
];


/**
 * Deals Status
 */
const DealsStatus = [
    {
        name: "Absternet LLC",
        date: 'Sep 20, 2021',
        profile: 'assets/images/users/avatar-1.jpg',
        userName: 'Donald Risher',
        status: "Deal Won",
        value: "100.1K"
    },
    {
        name: "Raitech Soft",
        date: 'Sep 23, 2021',
        profile: 'assets/images/users/avatar-2.jpg',
        userName: 'Sofia Cunha',
        status: "Intro Call",
        value: "150K"
    },
    {
        name: "William PVT",
        date: 'Sep 27, 2021',
        profile: 'assets/images/users/avatar-3.jpg',
        userName: 'Luis Rocha',
        status: "Stuck",
        value: "78.18K"
    },
    {
        name: "Loiusee LLP",
        date: 'Sep 30, 2021',
        profile: 'assets/images/users/avatar-4.jpg',
        userName: 'Vitoria Rodrigues',
        status: "Deal Won",
        value: "180K"
    },
    {
        name: "Apple Inc.",
        date: 'Sep 30, 2021',
        profile: 'assets/images/users/avatar-6.jpg',
        userName: 'Vitoria Rodrigues',
        status: "New Lead",
        value: "78.9K"
    }
];

/**
 * Upcoming Activities
 */
const UpcomingActivities = [
    {
        date: "25",
        day: 'Tue',
        time: '12:00am - 03:30pm',
        content: 'Meeting for campaign with sales team',
        users: [
            {
                name: 'Stine Nielsen',
                profile: 'assets/images/users/avatar-1.jpg'
            },
            {
                name: 'Jansh Brown',
                profile: 'assets/images/users/avatar-2.jpg'
            },
            {
                name: 'Dan Gibson',
                profile: 'assets/images/users/avatar-3.jpg'
            },
            {
                name: '5',
                variant: "bg-info"
            }
        ]
    },
    {
        date: "20",
        day: 'Wed',
        time: '02:00pm - 03:45pm',
        content: 'Adding a new event with attachments',
        users: [
            {
                name: 'Frida Bang',
                profile: 'assets/images/users/avatar-4.jpg'
            },
            {
                name: 'Malou Silva',
                profile: 'assets/images/users/avatar-5.jpg'
            },
            {
                name: 'Simon Schmidt',
                profile: 'assets/images/users/avatar-6.jpg'
            },
            {
                name: 'Tosh Jessen',
                profile: 'assets/images/users/avatar-7.jpg'
            },
            {
                name: '3',
                variant: "bg-success"
            }
        ]
    },
    {
        date: "17",
        day: 'Wed',
        time: '04:30pm - 07:15pm',
        content: 'Create new project Bundling Product',
        users: [
            {
                name: 'Nina Schmidt',
                profile: 'assets/images/users/avatar-8.jpg'
            },
            {
                name: 'Stine Nielsen',
                profile: 'assets/images/users/avatar-1.jpg'
            },
            {
                name: 'Jansh Brown',
                profile: 'assets/images/users/avatar-2.jpg'
            },
            {
                name: '4',
                variant: "bg-primary"
            }
        ]
    },
    {
        date: "12",
        day: 'Tue',
        time: '10:30am - 01:15pm',
        content: 'Weekly closed sales won checking with sales team',
        users: [
            {
                name: 'Stine Nielsen',
                profile: 'assets/images/users/avatar-1.jpg'
            },
            {
                name: 'Jansh Brown',
                profile: 'assets/images/users/avatar-5.jpg'
            },
            {
                name: 'Dan Gibson',
                profile: 'assets/images/users/avatar-2.jpg'
            },
            {
                name: '9',
                variant: "bg-warning"
            }
        ]
    }
];

/**
 * Closing Deals
 */
const ClosingDeals = [
    {
        name: "Acme Inc Install",
        profile: 'assets/images/users/avatar-1.jpg',
        userName: 'Donald Risher',
        amount: "96k",
        date: "Today"
    },
    {
        name: "Save lots Stores",
        profile: 'assets/images/users/avatar-2.jpg',
        userName: 'Jansh Brown',
        amount: "55.7k",
        date: "30 Dec 2021"
    },
    {
        name: "William PVT",
        profile: 'assets/images/users/avatar-7.jpg',
        userName: 'Ayaan Hudda',
        amount: "102k",
        date: "25 Nov 2021"
    },
    {
        name: "Raitech Soft",
        profile: 'assets/images/users/avatar-4.jpg',
        userName: 'Julia William',
        amount: "89.5k",
        date: "20 Sep 2021"
    },
    {
        name: "Absternet LLC",
        profile: 'assets/images/users/avatar-4.jpg',
        userName: 'Vitoria Rodrigues',
        amount: "89.5k",
        date: "20 Sep 2021"
    }
];


export { statData, DealsStatus, UpcomingActivities, ClosingDeals };
