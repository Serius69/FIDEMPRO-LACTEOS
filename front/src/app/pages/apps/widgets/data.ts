import { ChartOptions } from './widgets.model';

/**
 * Series Data
 */
function generateData(count: number, yrange: { max: number; min: number; }) {
    var i = 0;
    var series = [];
    while (i < count) {
        var x = "w" + (i + 1).toString();
        var y =
            Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

        series.push({
            x: x,
            y: y
        });
        i++;
    }
    return series;
}

/**
 * Group List
 */
const tileBoxs1 = [
    {
        id: 1,
        label: "Total Earnings",
        labelClass: "muted",
        percentage: "+16.24 %",
        percentageClass: "success",
        percentageIcon: "ri-arrow-right-up-line",
        counter: 559.25,
        caption: "View net earnings",
        icon: "bx bx-dollar-circle",
        iconClass: "bg-success-subtle text-success",
        decimals: 2,
        prefix: "$",
        suffix: "k",
    },
    {
        id: 2,
        label: "Orders",
        labelClass: "white-50",
        percentage: "-3.57 %",
        percentageClass: "warning",
        percentageIcon: "ri-arrow-right-down-line",
        counter: 36894,
        caption: "View all orders",
        icon: "bx bx-shopping-bag",
        iconClass: "bg-white bg-opacity-25",
        bgColor: "bg-info",
        counterClass: "text-white",
        captionClass: "text-white-50",
        decimals: 1,
        prefix: "",
        suffix: "",
    },
    {
        id: 3,
        label: "Customers",
        labelClass: "muted",
        percentage: "+29.08 %",
        percentageClass: "success",
        percentageIcon: "ri-arrow-right-up-line",
        counter: 183.35,
        caption: "See details",
        icon: "bx bx-user-circle",
        iconClass: "bg-warning-subtle text-warning",
        decimals: 2,
        prefix: "",
        suffix: "M",
    },
    {
        id: 4,
        label: "My Balance",
        labelClass: "muted",
        percentage: "+0.00 %",
        percentageClass: "muted",
        percentageIcon: "ri-arrow-right-up-line",
        counter: 165.89,
        caption: "Withdraw money",
        icon: "bx bx-wallet",
        iconClass: "bg-primary-subtle text-primary",
        decimals: 2,
        prefix: "$",
        suffix: "K",
    },
]

// TitleBoxs2
const tileBoxs2 = [
    {
        id: 1,
        label: "Campaign Sent",
        badge: "ri-arrow-up-circle-line text-success",
        icon: "ri-space-ship-line",
        counter: 197,
        decimals: 0,
        suffix: "",
        prefix: "",
    },
    {
        id: 2,
        label: "Annual Profit",
        badge: "ri-arrow-up-circle-line text-success",
        icon: "ri-exchange-dollar-line",
        counter: 489.4,
        decimals: 1,
        suffix: "k",
        prefix: "$",
    },
    {
        id: 3,
        label: "Lead Conversation",
        badge: "ri-arrow-down-circle-line text-danger",
        icon: "ri-pulse-line",
        counter: 32.89,
        decimals: 2,
        suffix: "%",
        prefix: "",
    },
    {
        id: 4,
        label: "Daily Average Income",
        badge: "ri-arrow-up-circle-line text-success",
        icon: "ri-trophy-line",
        counter: 1596.5,
        decimals: 1,
        prefix: "$",
        separator: ",",
        suffix: "",
    },
    {
        id: 5,
        label: "Annual Deals",
        badge: "ri-arrow-down-circle-line text-danger",
        icon: "ri-service-line",
        counter: 2659,
        decimals: 0,
        separator: ",",
        suffix: "",
        prefix: "",
    },
];

// tileBoxs3
const tileBoxs3 = [
    {
        id: 1,
        label: "Users",
        labelClass: "muted",
        counter: 28.05,
        badgeClass: "bg-light text-success",
        badge: "ri-arrow-up-line",
        percentage: "16.24 %",
        iconClass: "bg-info-subtle text-info",
        feaIcon: "users",
        subCounter: [
            {
                id: 1,
                counter: 28.05,
                decimals: 2,
                suffix: "k",
                prefix: "",
            },
        ],
    },
    {
        id: 2,
        label: "Sessions",
        labelClass: "muted",
        badgeClass: "bg-light text-danger",
        badge: "ri-arrow-down-line",
        percentage: "3.96 %",
        iconClass: "bg-info-subtle text-info",
        feaIcon: "activity",
        subCounter: [
            {
                id: 1,
                counter: 97.66,
                decimals: 2,
                suffix: "k",
                prefix: "",
            },
        ],
    },
    {
        id: 3,
        bgColor: "bg-primary",
        label: "Avg. Visit Duration",
        labelClass: "white-50",
        counterClass: "text-white",
        badgeClass: "bg-light-subtle text-body",
        badge: "ri-arrow-down-line",
        percentage: "0.24 %",
        iconClass: "bg-white bg-opacity-25",
        feaIcon: "clock",
        decimals: 0,
        suffix: "",
        prefix: "",
        subCounter: [
            {
                id: 1,
                counter: 3,
                decimals: 1,
                suffix: "m ",
                prefix: "",
            },
            {
                id: 2,
                counter: 40,
                decimals: 1,
                suffix: "sec",
                prefix: "",
            },
        ],
    },
    {
        id: 4,
        label: "Bounce Rate",
        labelClass: "muted",
        badgeClass: "bg-light text-success",
        badge: "ri-arrow-up-line",
        percentage: "7.05 %",
        iconClass: "bg-info-subtle text-info",
        feaIcon: "external-link",
        subCounter: [
            {
                id: 1,
                counter: 33.48,
                decimals: 2,
                suffix: "%",
                prefix: "",
            },
        ],
    },
];

// tileBoxes4
const tileBoxs4 = [
    {
        id: 1,
        bgColor: "bg-success",
        icon: "bx bx-shopping-bag",
        iconClass: "bg-white bg-opacity-25",
        label: "Total Sales",
        labelClass: "white-50",
        counter: 2045,
        counterClass: "text-white",
        caption: "From 1930 last year",
        captionClass: "white-50",
        percentage: "6.11 %",
        percentageClass: "bg-white bg-opacity-25",
        badge: "ri-arrow-up-s-line",
        decimals: 1,
        separator: ",",
        suffix: "",
        prefix: "",
    },
    {
        id: 2,
        icon: "bx bxs-user-account",
        iconClass: "bg-warning-subtle text-warning",
        label: "Number of Users",
        labelClass: "muted",
        counter: 7522,
        caption: "From 9530 last year",
        captionClass: "muted",
        percentage: "10.35 %",
        percentageClass: "bg-danger-subtle text-danger",
        badge: "ri-arrow-down-s-line",
        decimals: 1,
        separator: ",",
        suffix: "",
        prefix: "",
    },
    {
        id: 3,
        icon: "bx bxs-badge-dollar",
        iconClass: "bg-danger-subtle text-danger",
        label: "Total Revenue",
        labelClass: "muted",
        counter: 2845.05,
        caption: "From $1,750.04 last year",
        captionClass: "muted",
        percentage: "22.96 %",
        percentageClass: "bg-success-subtle text-success",
        badge: "ri-arrow-up-s-line",
        decimals: 2,
        separator: ",",
        suffix: "",
        prefix: "$",
    },
    {
        id: 4,
        icon: "bx bx-store-alt",
        iconClass: "bg-info-subtle text-info",
        label: "Number of Stores",
        labelClass: "muted",
        counter: 405,
        caption: "From 308 last year",
        captionClass: "muted",
        percentage: "16.31 %",
        percentageClass: "bg-success-subtle text-success",
        badge: "ri-arrow-up-s-line",
        decimals: 1,
        separator: ",",
        suffix: "k",
        prefix: "",
    },
];

// tileBoxes5
const tileBoxs5 = [
    {
        id: 1,
        icon: "assets/images/companies/img-3.png",
        label: "Marketing Director",
        experience: '2-4 Yrs Exp.',
        companyname: 'Themesbrand',
        location: 'California'
    },
    {
        id: 2,
        icon: "assets/images/companies/img-4.png",
        label: "Sr. Web Designer",
        experience: '2+ Yrs Exp.',
        companyname: 'Themesbrand',
        location: 'California'
    },
    {
        id: 3,
        bgColor: 'bg-primary-subtle',
        icon: "assets/images/companies/img-6.png",
        label: "Sr. Web Designer",
        experience: '2+ Yrs Exp.',
        companyname: 'Themesbrand',
        location: 'California'
    },
    {
        id: 4,
        bgColor: 'bg-info-subtle',
        icon: "assets/images/companies/img-8.png",
        label: "Sr. Web Designer",
        experience: '2+ Yrs Exp.',
        companyname: 'Themesbrand',
        location: 'California'
    },
];

// otherWidgets
const otherWidgets = [
    {
        id: 1,
        title: "Brand Logo Design - MD",
        subTitle: "Graphics Work",
        subItem: [
            {
                id: 1,
                icon: "mdi mdi-numeric-1-circle",
                iconClass: "success",
                label: "Completed",
            },
            {
                id: 2,
                icon: "mdi mdi-numeric-3-circle",
                iconClass: "info",
                label: "In Progress",
            },
            {
                id: 3,
                icon: "mdi mdi-numeric-2-circle",
                iconClass: "primary",
                label: "To Do",
            },
        ],
        progressBar: [
            { id: 1, bgColor: "bg-success", width: 30 },
            { id: 2, bgColor: "bg-info", width: 50 },
            { id: 3, width: 20 },
        ],
    },
    {
        id: 2,
        title: "Redesign - Landing Page",
        subTitle: "UI/UX Design",
        subItem: [
            {
                id: 1,
                icon: "mdi mdi-numeric-3-circle",
                iconClass: "success",
                label: "Completed",
            },
            {
                id: 2,
                icon: "mdi mdi-numeric-0-circle",
                iconClass: "info",
                label: "In Progress",
            },
            {
                id: 3,
                icon: "mdi mdi-numeric-8-circle",
                iconClass: "primary",
                label: "To Do",
            },
        ],
        progressBar: [
            { id: 1, bgColor: "bg-success", width: "30%" },
            { id: 2, bgColor: "bg-info", width: "0%" },
            { id: 3, width: "70%" },
        ],
    },
    {
        id: 3,
        title: "Ecommerce App for Web",
        subTitle: "CRM Project",
        subItem: [
            {
                id: 1,
                icon: "mdi mdi-numeric-10-circle",
                iconClass: "success",
                label: "Completed",
            },
            {
                id: 2,
                icon: "mdi mdi-numeric-8-circle",
                iconClass: "info",
                label: "In Progress",
            },
            {
                id: 3,
                icon: "mdi mdi-numeric-2-circle",
                iconClass: "primary",
                label: "To Do",
            },
        ],
        progressBar: [
            { id: 1, bgColor: "bg-success", width: "60%" },
            { id: 2, bgColor: "bg-info", width: "25%" },
            { id: 3, width: "15%" },
        ],
    },
];

// widgetsActivities
const widgetsActivities = [
    {
        id: 1,
        date: "25",
        weekDay: "Tue",
        time: "12:00am - 03:30pm",
        caption: "Meeting for campaign with sales team",
        subItem: [
            { id: 1, img: 'assets/images/users/avatar-1.jpg', name: 'Stine Nielsen' },
            { id: 2, img: 'assets/images/users/avatar-2.jpg', name: 'Jansh Brown' },
            { id: 3, img: 'assets/images/users/avatar-3.jpg', name: 'Dan Gibson' },
            { id: 4, imgNumber: "5", bgcolor: "bg-info" },
        ],
    },
    {
        id: 2,
        date: "20",
        weekDay: "Wed",
        time: "02:00pm - 03:45pm",
        caption: "Adding a new event with attachments",
        subItem: [
            { id: 1, img: 'assets/images/users/avatar-4.jpg', name: 'Frida Bang' },
            { id: 2, img: 'assets/images/users/avatar-5.jpg', name: 'Frida Bang' },
            { id: 3, img: 'assets/images/users/avatar-6.jpg', name: 'Simon Schmidt' },
            { id: 4, img: 'assets/images/users/avatar-7.jpg', name: 'Tosh Jessen' },
            { id: 5, imgNumber: "3", bgcolor: "bg-success" },
        ],
    },
    {
        id: 3,
        date: "17",
        weekDay: "Wed",
        time: "04:30pm - 07:15pm",
        caption: "Create new project Bundling Product",
        subItem: [
            { id: 1, img: 'assets/images/users/avatar-8.jpg', name: 'Nina Schmidt' },
            { id: 2, img: 'assets/images/users/avatar-1.jpg', name: 'Stine Nielsen' },
            { id: 3, img: 'assets/images/users/avatar-2.jpg', name: 'Jansh Brown' },
            { id: 4, imgNumber: "4", bgcolor: "bg-primary" },
        ],
    },
    {
        id: 4,
        date: "12",
        weekDay: "Tue",
        time: "10:30am - 01:15pm",
        caption: "Weekly closed sales won checking with sales team",
        subItem: [
            { id: 1, img: 'assets/images/users/avatar-1.jpg', name: 'Stine Nielsen' },
            { id: 2, img: 'assets/images/users/avatar-5.jpg', name: 'Jansh Brown' },
            { id: 3, img: 'assets/images/users/avatar-2.jpg', name: 'Dan Gibson' },
            { id: 4, imgNumber: "9", bgcolor: "bg-warning" },
        ],
    },
];

// widgetsTasks
const widgetsTasks = [
    {
        id: 1,
        forId: "task_one",
        text: "Review and make sure nothing slips through cracks",
        date: "15 Sep, 2021",
    },
    {
        id: 2,
        forId: "task_two",
        text: "Send meeting invites for sales upcampaign",
        date: "20 Sep, 2021",
    },
    {
        id: 3,
        forId: "task_three",
        text: "Weekly closed sales won checking with sales team",
        date: "24 Sep, 2021",
    },
    {
        id: 4,
        forId: "task_four",
        text: "Add notes that can be viewed from the individual view",
        date: "27 Sep, 2021",
    },
    {
        id: 5,
        forId: "task_five",
        text: "Move stuff to another page",
        date: "27 Sep, 2021",
    },
    {
        id: 6,
        forId: "task_six",
        text: "Styling wireframe design and documentation for velzon admin",
        date: "27 Sep, 2021",
    },
];

// Hot Product

const hotproducts = [
    {
        id: '1',
        image: 'assets/images/products/img-3.png',
        price: '99.94',
        name: '350 ml Glass Grocery Container'
    },
    {
        id: '2',
        image: 'assets/images/products/img-4.png',
        price: '99.94',
        name: 'Fabric Dual Tone Living Room Chair'
    },
    {
        id: '3',
        image: 'assets/images/products/img-5.png',
        price: '99.94',
        name: 'Crux Motorsports Helmet'
    },
    {
        id: '4',
        image: 'assets/images/products/img-6.png',
        price: '99.94',
        name: 'Half Sleeve T-Shirts (Blue)'
    }
]

// candidate
const candidate = [
    {
        id: '1',
        image: 'assets/images/users/avatar-2.jpg',
        name: 'Anna Adame',
        insta: 'Anna',
        designation: 'Web Developer'
    },
    {
        id: '2',
        image: 'assets/images/users/avatar-1.jpg',
        name: 'Patricia Cavin',
        insta: 'Patricia',
        designation: 'Web Developer'
    },
    {
        id: '3',
        image: 'assets/images/users/avatar-3.jpg',
        name: 'Jason Tran',
        insta: 'Jason',
        designation: 'Magento Developer'
    },
    {
        id: '4',
        image: 'assets/images/users/avatar-4.jpg',
        name: 'Cheryl Moore',
        insta: 'Cheryl',
        designation: 'Product Designer'
    },
    {
        id: '5',
        image: 'assets/images/users/avatar-5.jpg',
        name: 'Jennifer Bailey',
        insta: 'Jennifer',
        designation: 'Marketing Director'
    }
]

const bank = [
    {
        id: '1',
        icon: 'visa-fill',
        cardcolor: 'success',
        card: 'Visa Card',
        amount: '8,500',
        state: true
    },
    {
        id: '2',
        icon: 'bank-card-2-line',
        cardcolor: 'info',
        card: 'Credit Card',
        amount: '8,326'
    },
    {
        id: '3',
        icon: 'mastercard-line',
        cardcolor: 'danger',
        card: 'Mastercard Card',
        amount: '8,400'
    }
]

export { tileBoxs1, tileBoxs2, tileBoxs3, tileBoxs4, otherWidgets, widgetsActivities, widgetsTasks, tileBoxs5, hotproducts, candidate, bank };
