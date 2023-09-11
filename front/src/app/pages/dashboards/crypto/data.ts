import { ChartOptions } from './crypto.model';

/**
 * Stat Counder Data
 */
 const statData = [{
    title: 'TOTAL INVESTED',
    value: 2390.68,
    icon: 'ri-money-dollar-circle-fill',
    persantage: '6.24',
    profit: 'up'
  }, {
    title: 'TOTAL CHANGE',
    value: 19523.25,
    icon: 'ri-arrow-up-circle-fill',
    persantage: '3.67',
    profit: 'up'
  }, {
    title: 'DAY CHANGE',
    value: 14799.44,
    icon: 'ri-arrow-down-circle-fill',
    persantage: '4.80',
    profit: 'down'
  }
];

/**
 * BitCoin Chart
 */
 const BitcoinChart: ChartOptions = {
  series: [{
    name: "Bitcoin",
    data: [85, 68, 35, 90, 8, 11, 26, 54]
  }, ],
  chart: {
    width: 130,
    height: 50,
    type: "area",
    sparkline: {
        enabled: true,
    },
    toolbar: {
        show: false,
    }
  },
  dataLabels: {
    enabled: false,
  },
  stroke: {
    curve: "smooth",
    width: 1.5,
  },
  fill: {
    type: "gradient",
    gradient: {
        shadeIntensity: 1,
        inverseColors: false,
        opacityFrom: 0.45,
        opacityTo: 0.05,
        stops: [50, 100, 100, 100],
    },
  },
  colors: ["#0ab39c"]
};

/**
 * Lite Coin Chart
 */
 const litecoinChart: ChartOptions = {
  series: [{
    name: "Litecoin",
    data: [25, 50, 41, 87, 12, 36, 9, 54]
  }, ],
  chart: {
      width: 130,
      height: 46,
      type: "area",
      sparkline: {
          enabled: true,
      },
      toolbar: {
          show: false,
      },
  },
  dataLabels: {
      enabled: false,
  },
  stroke: {
      curve: "smooth",
      width: 1.5,
  },
  fill: {
      type: "gradient",
      gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
      },
  },
  colors: ["#0ab39c"]
};

/**
 * Eatherreum Chart
 */
 const EatherreumChart: ChartOptions = {
  series: [{
    name: "Ethereum",
    data: [36, 21, 65, 22, 35, 50, 29, 44]
  }, ],
  chart: {
      width: 130,
      height: 46,
      type: "area",
      sparkline: {
          enabled: true,
      },
      toolbar: {
          show: false,
      },
  },
  dataLabels: {
      enabled: false,
  },
  stroke: {
      curve: "smooth",
      width: 1.5,
  },
  fill: {
      type: "gradient",
      gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
      },
  },
  colors: ["#0ab39c"]
};

/**
 * Binance Chart
 */
 const BinanceChart: ChartOptions = {
  series: [{
    name: "Binance",
    data: [30, 58, 29, 89, 12, 36, 9, 54]
  }, ],
  chart: {
      width: 130,
      height: 46,
      type: "area",
      sparkline: {
          enabled: true,
      },
      toolbar: {
          show: false,
      },
  },
  dataLabels: {
      enabled: false,
  },
  stroke: {
      curve: "smooth",
      width: 1.5,
  },
  fill: {
      type: "gradient",
      gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
      },
  },
  colors: ["#f06548"]
};

/**
 * Dash Chart
 */
 const DashChart: ChartOptions = {
  series: [{
    name: "Dash",
    data: [24, 68, 39, 86, 29, 42, 11, 58]
}, ],
  chart: {
      width: 130,
      height: 46,
      type: "area",
      sparkline: {
          enabled: true,
      },
      toolbar: {
          show: false,
      },
  },
  dataLabels: {
      enabled: false,
  },
  stroke: {
      curve: "smooth",
      width: 1.5,
  },
  fill: {
      type: "gradient",
      gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
      },
  },
  colors: ["#0ab39c"]
};

/**
 * Tether Chart
 */
 const TetherChart: ChartOptions = {
  series: [{
    name: "Dash",
    data: [13, 76, 12, 85, 25, 60, 9, 54]
  }, ],
  chart: {
      width: 130,
      height: 46,
      type: "area",
      sparkline: {
          enabled: true,
      },
      toolbar: {
          show: false,
      },
  },
  dataLabels: {
      enabled: false,
  },
  stroke: {
      curve: "smooth",
      width: 1.5,
  },
  fill: {
      type: "gradient",
      gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
      },
  },
  colors: ["#0ab39c"]
};

/**
 * NEO Chart
 */
 const NeoChart: ChartOptions = {
  series: [{
    name: "Neo",
    data: [9, 66, 41, 89, 12, 36, 25, 54]
  }, ],
  chart: {
      width: 130,
      height: 46,
      type: "area",
      sparkline: {
          enabled: true,
      },
      toolbar: {
          show: false,
      },
  },
  dataLabels: {
      enabled: false,
  },
  stroke: {
      curve: "smooth",
      width: 1.5,
  },
  fill: {
      type: "gradient",
      gradient: {
          shadeIntensity: 1,
          inverseColors: false,
          opacityFrom: 0.45,
          opacityTo: 0.05,
          stops: [50, 100, 100, 100],
      },
  },
  colors: ["#f06548"]
};

/**
 * New Currencies
 */
 const Currencies = [
  {
    image: "assets/images/svg/crypto-icons/btc.svg",
    coinName: "Bitcoin",
    price: '48,568.025',
    change: '5.26',
    profit: 'up',
    balance: '53,914.025',
    coin: '1.25634801',
  },
  {
    image: "assets/images/svg/crypto-icons/ltc.svg",
    coinName: "Litecoin",
    price: '87,142.027',
    change: '3.07',
    profit: 'down',
    balance: '75,854.127',
    coin: '2.85472161',
  },
  {
    image: "assets/images/svg/crypto-icons/eth.svg",
    coinName: "Ethereum",
    price: '33,847.961',
    change: '7.13',
    profit: 'up',
    balance: '44,152.185',
    coin: '1.45612347',
  },
  {
    image: "assets/images/svg/crypto-icons/bnb.svg",
    coinName: "Binance",
    price: '73,654.421',
    change: '0.97',
    profit: 'up',
    balance: '48,367.125',
    coin: '0.35734601',
  },
  {
    image: "assets/images/svg/crypto-icons/usdt.svg",
    coinName: "Tether",
    price: '66,742.077',
    change: '1.08',
    profit: 'down',
    balance: '53,487.083',
    coin: '3.62912570',
  },
  {
    image: "assets/images/svg/crypto-icons/dash.svg",
    coinName: "Dash",
    price: '34,736.209',
    change: '4.52',
    profit: 'up',
    balance: '15,203.347',
    coin: '1.85412740',
  },
  {
    image: "assets/images/svg/crypto-icons/neo.svg",
    coinName: "Neo",
    price: '56,357.313',
    change: '2.87',
    profit: 'down',
    balance: '61,843.173',
    coin: '1.87732061',
  },
  {
    image: "assets/images/svg/crypto-icons/doge.svg",
    coinName: "Dogecoin",
    price: '62,357.649',
    change: '3.45',
    profit: 'up',
    balance: '54,843.173',
    coin: '0.95632087',
  }
];

/**
 * Top Performers
 */
 const TopPerformers = [
  {
    image: "assets/images/svg/crypto-icons/btc.svg",
    coinName: "Bitcoin",
    price: '18.7',
    change: '12,863.08',
    profit: 'up',
    balance: '67.21',
    percentage: '4.33',
  },
  {
    image: "assets/images/svg/crypto-icons/eth.svg",
    coinName: "Ethereum",
    price: '27.4',
    change: '08,256.04',
    profit: 'up',
    balance: '51.19',
    percentage: '5.64',
  },
  {
    image: "assets/images/svg/crypto-icons/aave.svg",
    coinName: "Avalanche",
    price: '12.9',
    change: '11,896.13',
    profit: 'down',
    balance: '59.01',
    percentage: '4.08',
  },
  {
    image: "assets/images/svg/crypto-icons/doge.svg",
    coinName: "Dogecoin",
    price: '09.5',
    change: '15,999.06',
    profit: 'up',
    balance: '74.05',
    percentage: '3.12',
  },
  {
    image: "assets/images/svg/crypto-icons/bnb.svg",
    coinName: "Binance",
    price: '14.2',
    change: '13,786.18',
    profit: 'down',
    balance: '61.05',
    percentage: '9.22',
  },
  {
    image: "assets/images/svg/crypto-icons/ltc.svg",
    coinName: "Litecoin",
    price: '09.5',
    change: '10,604.27',
    profit: 'up',
    balance: '76.12',
    percentage: '4.92',
  }
];

/**
 * News Feed
 */
 const NewsFeed = [
  {
    image: "assets/images/small/img-1.jpg",
    content: "One stop shop destination on all the latest news in crypto currencies",
    date: 'Dec 12, 2021',
    time: '09:22 AM'
  },
  {
    image: "assets/images/small/img-2.jpg",
    content: "Coin Journal is dedicated to delivering stories on the latest crypto",
    date: 'Dec 03, 2021',
    time: '12:09 PM'
  },
  {
    image: "assets/images/small/img-3.jpg",
    content: "The bitcoin-holding U.S. senator is trying to “fully integrate” crypto",
    date: 'Nov 22, 2021',
    time: '11:47 AM'
  },
  {
    image: "assets/images/small/img-6.jpg",
    content: "Cryptocurrency price like Bitcoin, Dash, Dogecoin, Ripple and Litecoin",
    date: 'Nov 18, 2021',
    time: '06:13 PM'
  }
];

export { statData, BitcoinChart, litecoinChart, EatherreumChart, BinanceChart, DashChart, TetherChart, NeoChart, Currencies, TopPerformers, NewsFeed };
