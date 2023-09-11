/**
 * Monthly Price
 */

 const MonthlyPlan =  [
  {
      id : 1,
      type :"Starter",
      rate : 19,
      description : "The perfect way to get started and get used to our tools.",
      projects : 3,
      Customers :299,
      FTP:5,
      supportClass:"danger",
      supportClassSymbol :"close",
      storageClass :"danger",
      storageClassSymbol :"close",
      domainClass :"danger",
      domainClassSymbol :"close",
      ribbon:false,
      planButtonClassname: "danger"
  },
  {
      id : 2,
      type :"Professional",
      rate : 29,
      description : "Excellent for scalling teams to build culture. Special plan for professional business.",
      projects : 8,
      Customers :499,
      FTP:7,
      supportClass:"success",
      supportClassSymbol :"checkbox",
      storageClass :"danger",
      storageClassSymbol :"close",
      domainClass :"danger",
      domainClassSymbol :"close",
      ribbon:false,
      planButtonClassname: "success"
  },
  {
      id : 3,
      type :"Enterprise",
      rate : 39,
      description : "This plan is for those who have a team alredy and running a large business.",
      projects : 15,
      Customers :"Unlimited",
      FTP:12,
      supportClass:"success",
      supportClassSymbol :"checkbox",
      storageClass :"success",
      storageClassSymbol :"checkbox",
      domainClass :"danger",
      domainClassSymbol :"close",
      ribbon:true,
      planButtonClassname: "success"
  },
  {
      id : 4,
      type :"Unlimited",
      rate : 49,
      description : "For most businesses that want to optimize web queries.",
      projects : "Unlimited",
      Customers :"Unlimited",
      FTP:5,
      supportClass:"success",
      supportClassSymbol :"checkbox",
      storageClass :"success",
      storageClassSymbol :"checkbox",
      domainClass :"success",
      domainClassSymbol :"checkbox",
      ribbon:false,
      planButtonClassname: "success"
  },
]

/**
 * Yearly Price
 */

 const YearlyPlan =  [
  {
      id : 1,
      type :"Starter",
      rate : 171,
      price : 228,
      description : "The perfect way to get started and get used to our tools.",
      projects : 3,
      Customers :299,
      FTP:5,
      supportClass:"danger",
      supportClassSymbol :"close",
      storageClass :"danger",
      storageClassSymbol :"close",
      domainClass :"danger",
      domainClassSymbol :"close",
      ribbon:false,
      planButtonClassname: "danger"
  },
  {
      id : 2,
      type :"Professional",
      rate : 261,
      price: 348,
      description : "Excellent for scalling teams to build culture. Special plan for professional business.",
      projects : 8,
      Customers :499,
      FTP:7,
      supportClass:"success",
      supportClassSymbol :"checkbox",
      storageClass :"danger",
      storageClassSymbol :"close",
      domainClass :"danger",
      domainClassSymbol :"close",
      ribbon:false,
      planButtonClassname: "success"
  },
  {
      id : 3,
      type :"Enterprise",
      rate : 351,
      price: 468,
      description : "This plan is for those who have a team alredy and running a large business.",
      projects : 15,
      Customers :"Unlimited",
      FTP:12,
      supportClass:"success",
      supportClassSymbol :"checkbox",
      storageClass :"success",
      storageClassSymbol :"checkbox",
      domainClass :"danger",
      domainClassSymbol :"close",
      ribbon:true,
      planButtonClassname: "success"
  },
  {
      id : 4,
      type :"Unlimited",
      rate : 441,
      price: 588,
      description : "For most businesses that want to optimize web queries.",
      projects : "Unlimited",
      Customers :"Unlimited",
      FTP:5,
      supportClass:"success",
      supportClassSymbol :"checkbox",
      storageClass :"success",
      storageClassSymbol :"checkbox",
      domainClass :"success",
      domainClassSymbol :"checkbox",
      ribbon:false,
      planButtonClassname: "success"
  },
]


/**
 * Choose Plane
 */
const pricingPlan=[
  {
      id : 1,
      type :"Basic Plan",
      purpose :"For Startup",
      planIcon:"ri-book-mark-line",
      rate : 19,
      projects : 3,
      Customers :299,
      FTP:5,
      supportClass:"danger",
      supportClassSymbol :"close",
      storageClass :"danger",
      storageClassSymbol :"close",
      domainClass :"danger",
      domainClassSymbol :"close",
      ribbon:false,
      planButtonClassname: "soft-success"
  },
  {
    id : 2,
    type :"Pro Business",
    purpose :"Professional plans",
    planIcon:"ri-medal-line",
    rate : 29,
    projects : 15,
    Customers :"unlimited",
    FTP:12,
    supportClass:"success",
    supportClassSymbol :"checkbox",
    storageClass :"danger",
    storageClassSymbol :"close",
    domainClass :"danger",
    domainClassSymbol :"close",
    ribbon:true,
    planButtonClassname: "success"
  },
  {
      id : 3,
      type :"Platinum Plan",
      purpose :"Enterprise Businesses",
      planIcon:"ri-stack-line",
      rate : 39,
      projects : "unlimited",
      Customers :"unlimited",
      FTP:"unlimited",
      supportClass:"success",
      supportClassSymbol :"checkbox",
      storageClass :"success",
      storageClassSymbol :"checkbox",
      domainClass :"success",
      domainClassSymbol :"checkbox",
      ribbon:false,
      planButtonClassname: "soft-success"
  },
]

/**
 * Simple Plan
 */
const SimplePlan=[
  {
      id : 1,
      type :"Starter",
      purpose :"Starter plans",
      rate : 22,
      users : 1,
      storage : "01",
      domain:"No",
      support:"No",
      ribbon:false
  },
  {
      id : 2,
      type :"Starter",
      purpose :"Starter plans",
      rate : 29,
      users : 3,
      storage : "10",
      domain:"Yes",
      support:"No",
      ribbon:true
  },
  {
      id : 3,
      type :"Enterprise",
      purpose :"Enterprise plans",
      rate : 39,
      users : 3,
      storage : "20",
      domain:"Yes",
      support:"Yes",
      ribbon:true
  },
  {
      id : 4,
      type :"Unlimited",
      purpose :"Unlimited plans",
      rate : 49,
      users : 5,
      storage : "40",
      domain:"Yes",
      support:"Yes",
      ribbon:false
  },
]

export { MonthlyPlan, YearlyPlan, pricingPlan, SimplePlan };
