equations_data = [
  {
    "name": "Total Productos Vendidos",
    "description": "Ecuación para calcular el total de productos vendidos multiplicando el total de clientes atendidos por el promedio de ventas por cliente",
    "expression": "TPV = TCAE * VPC", 
    "variable1": "TPV",
    "variable2": "TCAE",
    "variable3": "VPC",
    "area": "Ventas"
  },

  {
    "name": "Total Productos Producidos",
    "description": "Ecuación para calcular el total de productos producidos multiplicando la capacidad de producción por el número promedio de productos producidos por empleado",
    "expression": "TPPRO = CP * NEPP",
    "variable1": "TPPRO",
    "variable2": "CP",
    "variable3": "NEPP",
    "area": "Producción"
  },

  {
    "name": "Demanda Insatisfecha",
    "description": "Ecuación para calcular la demanda insatisfecha restando la demanda estimada menos los productos vendidos ",
    "expression": "DI = DE - TPV",
    "variable1": "DI",
    "variable2": "DE",
    "variable3": "TPV",
    "area": "Ventas"
  },

  {
    "name": "Ventas por Cliente",
    "description": "Ecuación para calcular el promedio de ventas por cliente dividiendo las ventas totales entre los clientes atendidos",
    "expression": "VPC = TPV / TCAE",
    "variable1": "VPC",
    "variable2": "TPV",
    "variable3": "TCAE",
    "area": "Ventas"
  },

  {
    "name": "Ingresos Totales",
    "description": "Ecuación para calcular los ingresos totales multiplicando las ventas totales por el precio de venta unitario",
    "expression": "IT = TPV * PVP",
    "variable1": "IT",
    "variable2": "TPV",
    "variable3": "PVP",
    "area": "Contabilidad"
  },

  {
    "name": "Ganancias Totales",
    "description": "Ecuación para calcular las ganancias totales restando los ingresos totales menos los gastos totales",
    "expression": "GT = IT - GT",
    "variable1": "GT",
    "variable2": "IT",
    "variable3": "GT",
    "area": "Contabilidad"
  },

{
"name": "Gastos Operativos",
"description": "Ecuación para calcular los gastos operativos sumando costos fijos diarios, sueldos y salarios y costos de adquisición de insumos",
"expression": "GO = CFD + SE + CTAI",
"variable1": "GO",
"variable2": "CFD",
"variable3": "SE",
"variable4": "CTAI",
"area": "Contabilidad"
},
{
"name": "Gastos Generales",
"description": "Ecuación para calcular los gastos generales sumando los gastos operativos más los gastos de mercadeo y manejo",
"expression": "GG = GO + GMM",
"variable1": "GG",
"variable2": "GO",
"variable3": "GMM",
"area": "Contabilidad"
},
{
"name": "Costo Total Adquisición Insumos",
"description": "Ecuación para calcular el costo total de adquisición de insumos sumando el consumo unitario por insumo multiplicado por el costo unitario de cada insumo",
"expression": "CTAI = ∑ CUIP * CIP",
"variable1": "CTAI",
"variable2": "CUIP",
"variable3": "CIP",
"area": "Contabilidad"
},
{
"name": "Costo Total Reorden",
"description": "Ecuación para calcular el costo total de reorden de insumos sumando el costo de adquisición más los costos de preparación y entrega",

"expression": "CTR = CTAI + CUP",
"variable1": "CTR",
"variable2": "CTAI",
"variable3": "CUP",
"area": "Contabilidad"
},
{
"name": "Pedido Insumos",
"description": "Ecuación para calcular el monto total en dinero de cada pedido de insumos multiplicando el costo unitario por la cantidad solicitada",
"expression": "PI = CIP * CP",
"variable1": "PI",
"variable2": "CIP",
"variable3": "CP",
"area": "Contabilidad"
},
{
"name": "Uso de Inventario Insumos",
"description": "Ecuación para calcular el consumo de insumos del inventario multiplicando el consumo unitario del insumo por los productos producidos",
"expression": "UII = CIP * PP",
"variable1": "UII",
"variable2": "CIP",
"variable3": "PP",
"area": "Inventario Insumos"
},
  {
  "name": "Inventario Insumos",
  "description": "Ecuación para calcular el saldo de inventario de insumos sumando el inventario anterior más entradas menos salidas",
  "expression": "II = II + PI - UII",
  "variable1": "II",
  "variable2": "PI",
  "variable3": "UII",
  "area": "Inventario Insumos"
  },
{
  "name": "Inventario Productos Finales",
  "description": "Ecuación para calcular el saldo de inventario de productos finales sumando el inventario anterior más entradas de producción menos salidas por ventas",
  "expression": "IPF = IPF + PP - VPC",
  "variable1": "IPF",
  "variable2": "PP",
  "variable3": "VPC",
  "area": "Inventario Productos Finales"
  },
  {
    "name": "Nivel de Rentabilidad",
    "description": "Ecuación para calcular el nivel de rentabilidad, que es el porcentaje de utilidad sobre los ingresos totales",
    "expression": "NR = (IT - GT) / IT",
    "variable1": "NR",
    "variable2": "IT",
    "variable3": "GT",
    "area": "Contabilidad"
  },
  {
    "name": "Total Clientes Atendidos", 
    "description": "Ecuación para calcular el total de clientes atendidos multiplicando el número medio de clientes diarios por el número de días",
    "expression": "TCA = TCAE * NMD", 
    "variable1": "TCA",
    "variable2": "TCAE",
    "variable3": "NMD",
    "area": "Ventas"
  },
  {
    "name": "Costo Unitario Inventario",
    "description": "Ecuación para calcular el costo unitario del inventario, que es el costo total de producción dividido por el inventario de productos finales",
    "expression": "CUI = GT / IPF",
    "variable1": "CUI",
    "variable2": "GT",
    "variable3": "IPF",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Fijo Diario",
    "description": "Ecuación para calcular el costo fijo diario, que es el total de gastos operativos dividido por el número medio de días",
    "expression": "CFD = GO / NMD",
    "variable1": "CFD",
    "variable2": "GO",
    "variable3": "NMD",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Total Transporte",
    "description": "Ecuación para calcular el costo total de transporte multiplicando el costo unitario de producción por el tonelaje por vehículo",
    "expression": "CTT = CUP * TPV",
    "variable1": "CTT",
    "variable2": "CUP",
    "variable3": "TPV",
    "area": "Distribución"
  },
  {
    "name": "Costo Promedio Producción",
    "description": "Ecuación para calcular el costo promedio de producción, que es el costo total de producción dividido por el tonelaje por producto",
    "expression": "CPP = GT / TPP",
    "variable1": "CPP",
    "variable2": "GT",
    "variable3": "TPP",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Promedio Venta",
    "description": "Ecuación para calcular el costo promedio de venta, que es el costo total de producción dividido por el tonelaje por venta",
    "expression": "CPV = GT / TPV",
    "variable1": "CPV",
    "variable2": "GT",
    "variable3": "TPV",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Promedio Insumos",
    "description": "Ecuación para calcular el costo promedio de insumos, que es el costo total de insumos dividido por el tonelaje por venta",
    "expression": "CPI = CTAI / TPV",
    "variable1": "CPI",
    "variable2": "CTAI",
    "variable3": "TPV",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Promedio Mano Obra",
    "description": "Ecuación para calcular el costo promedio de mano de obra, que es el salario total de empleados dividido por el tonelaje por producto",
    "expression": "CPMO = SE / TPP",
    "variable1": "CPMO",
    "variable2": "SE",
    "variable3": "TPP",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Unitario Producción",
    "description": "Ecuación para calcular el costo unitario de producción, que es la suma del costo promedio de producción, el costo promedio de insumos y el costo promedio de mano de obra",
    "expression": "CUP = CPP + CPI + CPMO",
    "variable1": "CUP",
    "variable2": "CPP",
    "variable3": "CPI",
    "variable4": "CPMO",
    "area": "Contabilidad"
  },
  {
    "name": "Precio Venta Recomendado",
    "description": "Ecuación para calcular el precio de venta recomendado, que es el costo unitario de producción multiplicado por un factor de recargo",
    "expression": "PVR = CUP * (1 + NR)",
    "variable1": "PVR",
    "variable2": "CUP", 
    "variable3": "NR",
    "area": "Ventas"
  },
  {
    "name": "Capacidad Producción",
    "description": "Ecuación para calcular la capacidad de producción, que es el número medio de días multiplicado por el tonelaje por producto multiplicado por el número de empleados por producto",
    "expression": "CP = NMD * TPP * NEPP",
    "variable1": "CP",
    "variable2": "NMD",
    "variable3": "TPP",
    "variable4": "NEPP",
    "area": "Producción"
  },  
  {
    "name": "Factor Utilización",
    "description": "Ecuación para calcular el factor de utilización, que es el tonelaje por producto dividido por la capacidad de producción",
    "expression": "FU = TPP / CP",
    "variable1": "FU",
    "variable2": "TPP",
    "variable3": "CP",
    "area": "Producción"
  },
  {
    "name": "Productos Producidos",
    "description": "Ecuación para calcular el número de productos producidos, que es la capacidad de producción multiplicada por el número de artículos por lote de producción",
    "expression": "PP = CP * ALEP", 
    "variable1": "PP",
    "variable2": "CP", 
    "variable3": "ALEP",
    "area": "Producción"
  },
  {
    "name": "Total Gastos",
    "description": "Ecuación para calcular el total de gastos, que es la suma del costo total de producción, los gastos operativos y los gastos generales",
    "expression": "TG = GT + GO + GG",
    "variable1": "TG",
    "variable2": "GT",
    "variable3": "GO",
    "variable4": "GG",
    "area": "Contabilidad"
  },
  {
    "name": "Ingreso Bruto",
    "description": "Ecuación para calcular el ingreso bruto, que es la diferencia entre los ingresos totales y el total de gastos",
    "expression": "IB = IT - TG",
    "variable1": "IB", 
    "variable2": "IT",
    "variable3": "TG",
    "area": "Contabilidad" 
  },
  {
    "name": "Margen Bruto",
    "description": "Ecuación para calcular el margen bruto, que es el ingreso bruto dividido por los ingresos totales",
    "expression": "MB = IB / IT",
    "variable1": "MB",
    "variable2": "IB",
    "variable3": "IT",
    "area": "Contabilidad"
  },
  {
    "name": "Retorno Inversión",
    "description": "Ecuación para calcular el retorno de inversión, que es el ingreso bruto dividido por el costo total de producción",
    "expression": "RI = IB / GT",
    "variable1": "RI",
    "variable2": "IB",
    "variable3": "GT",
    "area": "Contabilidad"
  },
  {
    "name": "Rotación Inventario",
    "description": "Ecuación para calcular la rotación de inventario, que es el costo promedio de producción dividido por el inventario de productos finales",
    "expression": "RTI = CP / IPF",
    "variable1": "RTI",
    "variable2": "CP",
    "variable3": "IPF",
    "area": "Inventario Productos Finales" 
  },
  {
    "name": "Rotación Clientes",
    "description": "Ecuación para calcular la rotación de clientes, que es el total de ventas a crédito dividido por el total de cuentas por cobrar",
    "expression": "RTC = TPV / TCA",
    "variable1": "RTC",
    "variable2": "TPV",
    "variable3": "TCA",
    "area": "Realimentacion"
  },
  {
    "name": "Participación Mercado",
    "description": "Ecuación para calcular la participación de mercado, que es el total de ventas a crédito dividido por el tamaño del mercado",
    "expression": "PM = TPV / DH",
    "variable1": "PM",
    "variable2": "TPV",
    "variable3": "DH",
    "area": "Competencia"
  },
  {
    "name": "Productividad Empleados",
    "description": "Ecuación para calcular la productividad de los empleados, que es el total de ventas a crédito dividido por el número de empleados",
    "expression": "PE = TPV / SE",
    "variable1": "PE",
    "variable2": "TPV",
    "variable3": "SE",
    "area": "Recursos Humanos"
  },
  {
    "name": "Horas Ociosas",
    "description": "Ecuación para calcular las horas ociosas, que es el número medio de días multiplicado por 60 minutos, restado por el tonelaje por producto multiplicado por el tiempo de producción por empleado",
    "expression": "HO = NMD*60 - TPP*TE",  
    "variable1": "HO",
    "variable2": "NMD",
    "variable3": "TPP",
    "variable4": "TE",
    "area": "Recursos Humanos"
  },
  {
    "name": "Costo Horas Ociosas",
    "description": "Ecuación para calcular el costo de las horas ociosas, que es el número de horas ociosas multiplicado por el costo por minuto de ociosidad",
    "expression": "CHO = HO * CPMO",
    "variable1": "CHO",
    "variable2": "HO",
    "variable3": "CPMO",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Almacenamiento",
    "description": "Ecuación para calcular el costo de almacenamiento, que es el inventario de productos finales multiplicado por el costo unitario de almacenamiento",
    "expression": "CA = IPF * CUI", 
    "variable1": "CA",
    "variable2": "IPF",
    "variable3": "CUI",
    "area": "Inventario Productos Finales"
  }
]