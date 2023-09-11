// candidate list
const candidatelist = [
    {
        id: "1",
        img: "/assets/images/users/avatar-10.jpg",
        name: "Tonya Noble",
        designation: "Web Designer",
        location: "Cullera, Spain",
        type: "Part Time",
        rating: "4.2",
        ratingCount: "2.2k",
        bookmark: true
    }, {
        id: "2",
        img: "/assets/images/users/avatar-1.jpg",
        name: "Nicholas Ball",
        designation: "Assistant / Store Keeper",
        location: "San Lorenzo",
        type: "Full Time",
        rating: "4.1",
        ratingCount: "1.72k",
        bookmark: true
    }, {
        id: "3",
        img: "/assets/images/users/avatar-4.jpg",
        name: "Zynthia Marrow",
        designation: "Assistant / Store Keeper",
        location: "Cullera, Spain",
        type: "Freelancer",
        rating: "4.0",
        ratingCount: "42.5k",

    }, {
        id: "4",
        img: "/assets/images/users/avatar-2.jpg",
        name: "Philippa Santiago",
        designation: "Project Manager ",
        location: "Ugashik, US",
        type: "Part Time",
        rating: "4.3",
        ratingCount: "15k",
        bookmark: true
    }, {
        id: "5",
        img: "/assets/images/users/avatar-4.jpg",
        name: "Elizabeth Allen",
        designation: "Education Training ",
        location: "Zuweihir, UAE",
        type: "Freelancer",
        rating: "3.5",
        ratingCount: "7.3k",

    }, {
        id: "6",
        img: "/assets/images/users/avatar-5.jpg",
        name: "Cassian Jenning",
        designation: "Graphic Designer ",
        location: "Limestone, US",
        type: "Part Time",
        rating: "4.3",
        ratingCount: "13.2k",

    }, {
        id: "7",
        img: "/assets/images/users/avatar-6.jpg",
        name: "Scott Holt",
        designation: "UI/UX Designer ",
        location: "Germany",
        type: "Part Time",
        rating: "3.5",
        ratingCount: "7.3k",

    }, {
        id: "8",
        img: "/assets/images/users/avatar-9.jpg",
        name: "Philbert Schwartz",
        designation: "React Developer ",
        location: "Zuweihir, UAE",
        type: "Full Time",
        rating: "4.1",
        ratingCount: "1.74k",
        bookmark: true
    }, {
        id: "9",
        img: "/assets/images/users/avatar-2.jpg",
        name: "Larry Villa",
        designation: "Assistant / Store Keeper",
        location: "San Lorenzo",
        type: "Full Time",
        rating: "4.0",
        ratingCount: "1.72k",

    }, {
        id: "10",
        img: "/assets/images/users/avatar-10.jpg",
        name: "Harley Watkins",
        designation: "Project Manager ",
        location: "Texanna, US",
        type: "Full Time",
        rating: "4.2",
        ratingCount: "3.21k",

    }, {
        id: "11",
        img: "/assets/images/users/avatar-2.jpg",
        name: "Marie Stewart",
        designation: "Web Designer",
        location: "Cullera, Spain",
        type: "Part Time",
        rating: "4.2",
        ratingCount: "2.2k",
        bookmark: true
    }, {
        id: "12",
        img: "/assets/images/users/avatar-9.jpg",
        name: "Hadley Leonard",
        designation: "Executive, HR Operations ",
        location: "Zuweihir, UAE",
        type: "Full Time",
        rating: "4.0",
        ratingCount: "3.2k",

    }, {
        id: "13",
        img: "/assets/images/users/avatar-6.jpg",
        name: "Zoderick Rodriquez",
        designation: "Full Stack Developer",
        location: "Muhtarqah, UAE",
        type: "Freelancer",
        rating: "3.9",
        ratingCount: "98.65k",

    }, {
        id: "14",
        img: "/assets/images/users/avatar-7.jpg",
        name: "Nadia Harding",
        designation: "Web Designer",
        location: "Pahoa, US",
        type: "Freelancer",
        rating: "4.3",
        ratingCount: "2.93k",
        bookmark: true
    }, {
        id: "15",
        img: "/assets/images/users/avatar-1.jpg",
        name: "Addison Black",
        designation: "UI/UX Designer",
        location: "Phoenix, Arizona",
        type: "Part Time",
        rating: "3.8",
        ratingCount: "10.32k",

    }, {
        id: "16",
        img: "/assets/images/users/avatar-4.jpg",
        name: "Priscilla Wise",
        designation: "Executive, HR Operations",
        location: "Ghurayfah, UAE",
        type: "Full Time",
        rating: "4.0",
        ratingCount: "7.36k",

    }, {
        id: "17",
        img: "/assets/images/users/avatar-8.jpg",
        name: "Lizzie Chandler",
        designation: "React Developer",
        location: "Maidaq, UAE",
        type: "Part Time",
        rating: "3.9",
        ratingCount: "1.35k",

    }, {
        id: "18",
        img: "/assets/images/users/avatar-1.jpg",
        name: "Jenson Carlson",
        designation: "Graphic Designer",
        location: "Quesada, US",
        type: "Freelancer",
        rating: "4.2",
        ratingCount: "3.16k",

    }, {
        id: "19",
        img: "/assets/images/users/avatar-1.jpg",
        name: "Jaylee Ward",
        designation: "Education Training",
        location: "Cullera, Spain",
        type: "Full Time",
        rating: "4.0",
        ratingCount: "3.21k",
        bookmark: true
    }, {
        id: "20",
        img: "/assets/images/users/avatar-2.jpg",
        name: "Trista Guerrero",
        designation: "Product Director",
        location: "Jereirah, UAE",
        type: "Full Time",
        rating: "4.1",
        ratingCount: "4.31k",

    }, {
        id: "21",
        img: "/assets/images/users/avatar-1.jpg",
        name: "James Stone",
        designation: "Graphic Designer",
        location: "Quesada, US",
        type: "Freelancer",
        rating: "4.2",
        ratingCount: "3.16k",

    }, {
        id: "22",
        img: "/assets/images/users/avatar-4.jpg",
        name: "Mike Watson",
        designation: "Product Director",
        location: "Jereirah, UAE",
        type: "Full Time",
        rating: "4.1",
        ratingCount: "4.13k",

    }, {
        id: "23",
        img: "/assets/images/users/avatar-9.jpg",
        name: "Mary Sak",
        designation: "Education Training",
        location: "Cullera, Spain",
        type: "Full Time",
        rating: "4.0",
        ratingCount: "3.21k",
        bookmark: true
    }, {
        id: "24",
        img: "/assets/images/users/avatar-8.jpg",
        name: "Roderick Jones",
        designation: "React Developer",
        location: "Maidaq, UAE",
        type: "Part Time",
        rating: "3.9",
        ratingCount: "1.35k",

    }
]

export { candidatelist }