equations_data = [
  {
    "name": "Total Productos Vendidos",
    "expression": "TPV = TCAE * VPC", 
    "variable1": "TPV",
    "variable2": "TCAE",
    "variable3": "VPC",
    "area": "Ventas"
  },

  {
    "name": "Total Productos Producidos",
    "expression": "TPP = CP * NEPP",
    "variable1": "TPP",
    "variable2": "CP",
    "variable3": "NEPP",
    "area": "Producción"
  },

  {  
    "name": "Demanda Insatisfecha",
    "expression": "DI = DE - TPV",
    "variable1": "DI",
    "variable2": "DE", 
    "variable3": "TPV",
    "area": "Ventas"
  },

  {
    "name": "Ventas por Cliente",
    "expression": "VPC = TPV / TCAE",
    "variable1": "VPC",
    "variable2": "TPV",
    "variable3": "TCAE",
    "area": "Ventas"
  },

  {
    "name": "Ingresos Totales",
    "expression": "IT = TPV * PVP",
    "variable1": "IT",
    "variable2": "TPV",
    "variable3": "PVP",
    "area": "Contabilidad"
  },

  {
    "name": "Ganancias Totales",
    "expression": "GT = IT - GT",
    "variable1": "GT", 
    "variable2": "IT",
    "variable3": "GT",
    "area": "Contabilidad"
  },

  {
    "name": "Gastos Operativos",
    "expression": "GO = CFD + SE + CTAI",
    "variable1": "GO",
    "variable2": "CFD",
    "variable3": "SE",
    "variable4": "CTAI",
    "area": "Contabilidad"
  },
  {
    "name": "Gastos Generales",
    "expression": "GG = GO + GMM",
    "variable1": "GG",
    "variable2": "GO",
    "variable3": "GMM",
    "area": "Contabilidad"
  },  
  {
    "name": "Costo Total Adquisición Insumos",
    "expression": "CTAI = ∑ CUIP * CIP",
    "variable1": "CTAI",
    "variable2": "CUIP",
    "variable3": "CIP",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Total Reorden", 
    "expression": "CTR = CTAI + CUP",
    "variable1": "CTR",
    "variable2": "CTAI",
    "variable3": "CUP",
    "area": "Contabilidad"
  },
  {
    "name": "Pedido Insumos",
    "expression": "PI = CIP * CP",
    "variable1": "PI",
    "variable2": "CIP",
    "variable3": "CP",
    "area": "Contabilidad"
  },
  {
    "name": "Uso de Inventario Insumos",
    "expression": "UII = CIP * PP",
    "variable1": "UII", 
    "variable2": "CIP",
    "variable3": "PP",
    "area": "Contabilidad"
  },
  {
    "name": "Inventario Insumos",
    "expression": "II = II + PI - UII",
    "variable1": "II",
    "variable2": "PI",
    "variable3": "UII",
    "area": "Contabilidad" 
  },
  {
    "name": "Inventario Productos Finales",
    "expression": "IPF = IPF + PP - VPC",
    "variable1": "IPF",
    "variable2": "PP",
    "variable3": "VPC",
    "area": "Contabilidad"
  },
  {
    "name": "Nivel de Rentabilidad",
    "expression": "NR = (IT - GT) / IT",
    "variable1": "NR",
    "variable2": "IT",
    "variable3": "GT",
    "area": "Contabilidad"
  },
  {
    "name": "Total Clientes Atendidos", 
    "expression": "TCA = TCAE * NMD", 
    "variable1": "TCA",
    "variable2": "TCAE",
    "variable3": "NMD",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Unitario Inventario",
    "expression": "CUI = GT / IPF",
    "variable1": "CUI",
    "variable2": "GT",
    "variable3": "IPF",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Fijo Diario",
    "expression": "CFD = GO / NMD",
    "variable1": "CFD",
    "variable2": "GO",
    "variable3": "NMD",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Total Transporte",
    "expression": "CTT = CUP * TPV",
    "variable1": "CTT",
    "variable2": "CUP",
    "variable3": "TPV",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Unitario Transporte",
    "expression": "CUT = CTT / TPV",  
    "variable1": "CUT",
    "variable2": "CTT",
    "variable3": "TPV",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Promedio Producción",
    "expression": "CPP = GT / TPP",
    "variable1": "CPP", 
    "variable2": "GT",
    "variable3": "TPP",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Promedio Venta",
    "expression": "CPV = GT / TPV",
    "variable1": "CPV",
    "variable2": "GT",
    "variable3": "TPV",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Promedio Insumos",
    "expression": "CPI = CTAI / TPV",
    "variable1": "CPI",
    "variable2": "CTAI",
    "variable3": "TPV",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Promedio Mano Obra",
    "expression": "CPMO = SE / TPP",
    "variable1": "CPMO",
    "variable2": "SE",
    "variable3": "TPP",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Unitario Producción",
    "expression": "CUP = CPP + CPI + CPMO",
    "variable1": "CUP",
    "variable2": "CPP",
    "variable3": "CPI",
    "variable4": "CPMO",
    "area": "Contabilidad"
  },
  {
    "name": "Precio Venta Recomendado",
    "expression": "PVR = CUP * (1 + NR)",
    "variable1": "PVR",
    "variable2": "CUP", 
    "variable3": "NR",
    "area": "Contabilidad"
  },
  {
    "name": "Capacidad Producción",
    "expression": "CP = NMD * TPP * NEPP",
    "variable1": "CP",
    "variable2": "NMD",
    "variable3": "TPP",
    "variable4": "NEPP",
    "area": "Contabilidad"
  },  
  {
    "name": "Factor Utilización",
    "expression": "FU = TPP / CP",
    "variable1": "FU",
    "variable2": "TPP",
    "variable3": "CP",
    "area": "Contabilidad"
  },
  {
    "name": "Productos Producidos",
    "expression": "PP = CP * ALEP", 
    "variable1": "PP",
    "variable2": "CP", 
    "variable3": "ALEP",
    "area": "Contabilidad"
  },
  {
    "name": "Total Gastos",
    "expression": "TG = GT + GO + GG",
    "variable1": "TG",
    "variable2": "GT",
    "variable3": "GO",
    "variable4": "GG",
    "area": "Contabilidad"
  },
  {
    "name": "Ingreso Bruto",
    "expression": "IB = IT - TG",
    "variable1": "IB", 
    "variable2": "IT",
    "variable3": "TG",
    "area": "Contabilidad" 
  },
  {
    "name": "Margen Bruto",
    "expression": "MB = IB / IT",
    "variable1": "MB",
    "variable2": "IB",
    "variable3": "IT",
    "area": "Contabilidad"
  },
  {
    "name": "Retorno Inversión",
    "expression": "RI = IB / GT",
    "variable1": "RI",
    "variable2": "IB",
    "variable3": "GT",
    "area": "Contabilidad"
  },
  {
    "name": "Rotación Inventario",
    "expression": "RTI = CP / IPF",
    "variable1": "RTI",
    "variable2": "CP",
    "variable3": "IPF",
    "area": "Contabilidad" 
  },
  {
    "name": "Rotación Clientes",
    "expression": "RTC = TPV / TCA",
    "variable1": "RTC",
    "variable2": "TPV",
    "variable3": "TCA",
    "area": "Contabilidad"
  },
  {
    "name": "Participación Mercado",
    "expression": "PM = TPV / DH",
    "variable1": "PM",
    "variable2": "TPV",
    "variable3": "DH",
    "area": "Contabilidad"
  },
  {
    "name": "Productividad Empleados",
    "expression": "PE = TPV / SE",
    "variable1": "PE",
    "variable2": "TPV",
    "variable3": "SE",
    "area": "Contabilidad"
  },
  {
    "name": "Horas Ociosas",
    "expression": "HO = NMD*60 - TPP*TE",  
    "variable1": "HO",
    "variable2": "NMD",
    "variable3": "TPP",
    "variable4": "TE",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Horas Ociosas",
    "expression": "CHO = HO * CPMO",
    "variable1": "CHO",
    "variable2": "HO",
    "variable3": "CPMO",
    "area": "Contabilidad"
  },
  {
    "name": "Costo Almacenamiento",
    "expression": "CA = IPF * CUI", 
    "variable1": "CA",
    "variable2": "IPF",
    "variable3": "CUI",
    "area": "Contabilidad"
  }
]