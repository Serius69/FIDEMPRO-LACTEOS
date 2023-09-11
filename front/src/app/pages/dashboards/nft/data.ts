import { color } from "echarts";

/**
 * Stat Counder Data
 */
const statData = [{
    icon: 'bx-dollar-circle',
    title: 'Total Revenue',
    value: 559526.564,
    persantage: '3.96',
    profit: 'down',
    bg_color: "danger"
},
{
    icon: 'bx-wallet',
    title: 'Estimated',
    value: 624562.564,
    persantage: '16.24',
    profit: 'up',
    bg_color: "success"
}
];

/**
 * featured NFT Data
 */
const featuredData = [
    {
        id: 1,
        img: 'https://img.themesbrand.com/velzon/images/img-3.gif',
        likes: "37.41k",
        title: "Walking On Air",
        category: "Artwork",
        highest: "10.35ETH",
        price: "14.167 ETH",
    },
    {
        id: 2,
        img: 'assets/images/nft/img-03.jpg',
        likes: "19.29k",
        title: "Filtered Portrait",
        category: "Photography",
        highest: "75.3ETH",
        price: "67.36 ETH",
    },
    {
        id: 3,
        img: 'https://img.themesbrand.com/velzon/images/img-1.gif',
        likes: "8.42k",
        title: "Patterns Arts & Culture",
        category: "Artwork",
        highest: "9.64ETH",
        price: "14.167 ETH",
    },
    {
        id: 4,
        img: 'https://img.themesbrand.com/velzon/images/img-4.gif',
        likes: "15.93k",
        title: "Evolved Reality",
        category: "Video",
        highest: "2.75ETH",
        price: "3.167 ETH",
    },
];

/**
 * Recent Nft Data
 */
const recentData = [
    {
        id: 1,
        img: 'assets/images/nft/img-01.jpg',
        title: "Abstract Face Painting",
        category: "Artworks",
        icon: 'assets/images/svg/crypto-icons/btc.svg',
        volume: "48,568.025",
        hours: 5.26,
        creators: "6.8K",
        items: "18.0K",
        iconClass: "trending-up",
        color: "text-success"
    },
    {
        id: 2,
        img: 'https://img.themesbrand.com/velzon/images/img-5.gif',
        title: "Long-tailed Macaque",
        category: "Games",
        icon: 'assets/images/svg/crypto-icons/ltc.svg',
        volume: "87,142.027",
        hours: 3.07,
        creators: "2.6K",
        items: "6.3K",
        textColor: true,
        iconClass: "trending-down",
        color: "text-danger"
    },
    {
        id: 3,
        img: 'assets/images/nft/img-06.jpg',
        title: "Robotic Body Art",
        category: "Photography",
        icon: 'assets/images/svg/crypto-icons/etc.svg',
        volume: "33,847.961",
        hours: 7.13,
        creators: "7.5K",
        items: "14.6K",
        iconClass: "trending-up",
        color: "text-success"
    },
    {
        id: 4,
        img: 'assets/images/nft/img-04.jpg',
        title: "Smillevers Crypto",
        category: "Artworks",
        icon: 'assets/images/svg/crypto-icons/dash.svg',
        volume: "73,654.421",
        hours: 0.97,
        creators: "5.3K",
        items: "36.4K",
        iconClass: "trending-up",
        color: "text-success"
    },
    {
        id: 5,
        img: 'assets/images/nft/img-03.jpg',
        title: "Creative Filtered Portrait",
        category: "3d Style",
        icon: 'assets/images/svg/crypto-icons/bnb.svg',
        volume: "66,742.077",
        hours: 1.08,
        creators: "3.1K",
        items: "12.4K",
        textColor: true,
        iconClass: "trending-down",
        color: "text-danger"
    },
    {
        id: 6,
        img: 'assets/images/nft/img-02.jpg',
        title: "The Chirstoper",
        category: "Crypto Card",
        icon: 'assets/images/svg/crypto-icons/usdt.svg',
        volume: "34,736.209",
        hours: 4.52,
        creators: "7.2K",
        items: "25.0K",
        iconClass: "trending-up",
        color: "text-success"
    },
];


/**
 * Top Collection Data
 */
const topCollectionData = [
    {
        id: 1,
        img: 'assets/images/nft/img-03.jpg',
        category: "Artworks",
        items: "4700+",
    },
    {
        id: 2,
        img: 'assets/images/nft/img-04.jpg',
        category: "Crypto Card",
        items: "743+",
    },
    {
        id: 3,
        img: 'https://img.themesbrand.com/velzon/images/img-5.gif',
        category: "3d Style",
        items: "4781+",
    },
    {
        id: 4,
        img: 'assets/images/nft/img-06.jpg',
        category: "Collectibles",
        items: "3468+",
    },
];

// popular Creators Data
const popularData = [
    {
        id: 1,
        img: 'assets/images/nft/img-02.jpg',
        author: "Alexis Clarke",
        price: "81,369 ETH",
    },
    {
        id: 2,
        img: 'assets/images/nft/img-01.jpg',
        author: "Timothy Smith",
        price: "4,754 ETH",
    },
    {
        id: 3,
        img: 'assets/images/nft/img-04.jpg',
        author: "Herbert Stokes",
        price: "68,945 ETH",
    },
    {
        id: 4,
        img: 'assets/images/users/avatar-1.jpg',
        author: "Glen Matney",
        price: "49,031 ETH",
    },
];

export { statData, featuredData, recentData, topCollectionData, popularData };