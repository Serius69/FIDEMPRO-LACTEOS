# equations_data.py - Versión Corregida con ecuaciones funcionales
equations_data = [
  # VENTAS - Ecuaciones base
  {
    "name": "Total clientes atendidos en el dia",
    "description": "Ecuación para la cantidad total de clientes que se tiene por dia",
    "expression": "TCAE = CPD * 0.95",  # Factor fijo en lugar de random()
    "variable1": "TCAE",
    "variable2": "CPD",
    "area": "Ventas"
  },
  
  {
    "name": "Total Productos Vendidos",
    "description": "Ecuación para calcular el total de productos vendidos",
    "expression": "TPV = TCAE * VPC", 
    "variable1": "TPV",
    "variable2": "TCAE",
    "variable3": "VPC",
    "area": "Ventas"
  },

  {
    "name": "Demanda Insatisfecha",
    "description": "Ecuación para calcular la demanda insatisfecha",
    "expression": "DI = max(0, DE - TPV)",
    "variable1": "DI",
    "variable2": "DE",
    "variable3": "TPV",
    "area": "Ventas"
  },

  {
    "name": "Ventas por Cliente",
    "description": "Ecuación para calcular el promedio de ventas por cliente",
    "expression": "VPC = TPV / max(TCAE, 1)",  # Evitar división por cero
    "variable1": "VPC",
    "variable2": "TPV",
    "variable3": "TCAE",
    "area": "Ventas"
  },

  {
    "name": "Total Clientes Atendidos", 
    "description": "Total de clientes atendidos en el período",
    "expression": "TCA = TCAE * NMD", 
    "variable1": "TCA",
    "variable2": "TCAE",
    "variable3": "NMD",
    "area": "Ventas"
  },

  {
    "name": "Frecuencia de Compra",
    "description": "Frecuencia de compra de los clientes",
    "expression": "FC = 1 / max(TPC, 0.1)",
    "variable1": "FC",
    "variable2": "TPC",
    "area": "Ventas"
  },

  # PRODUCCIÓN
  {
    "name": "Total Productos Producidos",
    "description": "Total de productos producidos según capacidad",
    "expression": "TPPRO = CPROD",  # Simplificado
    "variable1": "TPPRO",
    "variable2": "CPROD",
    "area": "Producción"
  },

  {
    "name": "Productos Producidos por Lote",
    "description": "Cantidad de productos lácteos producidos por lote",
    "expression": "PPL = CPROD * (CPPL / 1000)",  # Ajuste de escala
    "variable1": "PPL",
    "variable2": "CPROD",
    "variable3": "CPPL",  
    "area": "Producción"
  },

  {
    "name": "Capacidad de Producción Real",
    "description": "Capacidad de producción ajustada",
    "expression": "CPROD = QPL * NEPP",  # Simplificado
    "variable1": "CPROD",
    "variable2": "QPL",
    "variable3": "NEPP",
    "area": "Producción"
  },

  {
    "name": "Factor Utilización",
    "description": "Factor de utilización de la capacidad",
    "expression": "FU = min(TPV / max(CPROD, 1), 1)",  # Limitado a 1
    "variable1": "FU",
    "variable2": "TPV",
    "variable3": "CPROD",
    "area": "Producción"
  },

  # CONTABILIDAD - Ingresos
  {
    "name": "Ingresos Totales",
    "description": "Ingresos totales por ventas",
    "expression": "IT = TPV * PVP",
    "variable1": "IT",
    "variable2": "TPV",
    "variable3": "PVP",
    "area": "Contabilidad"
  },

  # CONTABILIDAD - Costos
  {
    "name": "Costo Total Adquisición Insumos",
    "description": "Costo total de insumos",
    "expression": "CTAI = CUIP * TPPRO",  # Simplificado
    "variable1": "CTAI",
    "variable2": "CUIP",
    "variable3": "TPPRO",
    "area": "Contabilidad"
  },

  {
    "name": "Gastos Operativos",
    "description": "Gastos operativos totales",
    "expression": "GO = CFD + (SE / 30) + CTAI",  # SE mensual a diario
    "variable1": "GO",
    "variable2": "CFD",
    "variable3": "SE",
    "variable4": "CTAI",
    "area": "Contabilidad"
  },

  {
    "name": "Gastos Generales",
    "description": "Gastos generales incluyendo marketing",
    "expression": "GG = GO + (GMM / 30)",  # GMM mensual a diario
    "variable1": "GG",
    "variable2": "GO",
    "variable3": "GMM",
    "area": "Contabilidad"
  },

  {
    "name": "Total Gastos",
    "description": "Total de gastos",
    "expression": "TG = GO + GG",  # Simplificado
    "variable1": "TG",
    "variable2": "GO",
    "variable3": "GG",
    "area": "Contabilidad"
  },

  {
    "name": "Ganancias Totales",
    "description": "Ganancias totales (ingresos menos gastos)",
    "expression": "GT = IT - TG",  # CORREGIDO
    "variable1": "GT",
    "variable2": "IT",
    "variable3": "TG",
    "area": "Contabilidad"
  },

  {
    "name": "Ingreso Bruto",
    "description": "Ingreso bruto",
    "expression": "IB = IT - TG",
    "variable1": "IB", 
    "variable2": "IT",
    "variable3": "TG",
    "area": "Contabilidad" 
  },

  {
    "name": "Margen Bruto",
    "description": "Margen bruto sobre ingresos",
    "expression": "MB = IB / max(IT, 1)",
    "variable1": "MB",
    "variable2": "IB",
    "variable3": "IT",
    "area": "Contabilidad"
  },

  {
    "name": "Nivel de Rentabilidad",
    "description": "Nivel de rentabilidad",
    "expression": "NR = GT / max(IT, 1)",  # CORREGIDO
    "variable1": "NR",
    "variable2": "GT",
    "variable3": "IT",
    "area": "Contabilidad"
  },

  {
    "name": "Retorno Inversión",
    "description": "Retorno de inversión",
    "expression": "RI = IB / max(abs(TG), 1)",  # CORREGIDO
    "variable1": "RI",
    "variable2": "IB",
    "variable3": "TG",
    "area": "Contabilidad"
  },

  # COSTOS UNITARIOS
  {
    "name": "Costo Promedio Producción",
    "description": "Costo promedio de producción",
    "expression": "CPP = TG / max(TPPRO, 1)",  # Por productos producidos
    "variable1": "CPP",
    "variable2": "TG",
    "variable3": "TPPRO",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Promedio Venta",
    "description": "Costo promedio de venta",
    "expression": "CPV = TG / max(TPV, 1)",
    "variable1": "CPV",
    "variable2": "TG",
    "variable3": "TPV",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Promedio Insumos",
    "description": "Costo promedio de insumos por venta",
    "expression": "CPI = CTAI / max(TPV, 1)",
    "variable1": "CPI",
    "variable2": "CTAI",
    "variable3": "TPV",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Promedio Mano Obra",
    "description": "Costo promedio de mano de obra",
    "expression": "CPMO = (SE / 30) / max(TPPRO, 1)",  # SE mensual a diario
    "variable1": "CPMO",
    "variable2": "SE",
    "variable3": "TPPRO",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Unitario Producción",
    "description": "Costo unitario de producción total",
    "expression": "CUP = CPP + CPI + CPMO",
    "variable1": "CUP",
    "variable2": "CPP",
    "variable3": "CPI",
    "variable4": "CPMO",
    "area": "Contabilidad"
  },

  {
    "name": "Precio Venta Recomendado",
    "description": "Precio de venta recomendado con margen",
    "expression": "PVR = CUP * (1 + max(NR, 0.2))",  # Mínimo 20% margen
    "variable1": "PVR",
    "variable2": "CUP", 
    "variable3": "NR",
    "area": "Ventas"
  },

  # INVENTARIOS
  {
    "name": "Pedido Insumos",
    "description": "Pedido de insumos según capacidad",
    "expression": "PI = CUIP * CPROD",
    "variable1": "PI",
    "variable2": "CUIP",
    "variable3": "CPROD",
    "area": "Inventario Insumos"
  },

  {
    "name": "Uso de Inventario Insumos",
    "description": "Consumo de insumos del inventario",
    "expression": "UII = CUIP * PPL",
    "variable1": "UII",
    "variable2": "CUIP",
    "variable3": "PPL",
    "area": "Inventario Insumos"
  },

  {
    "name": "Inventario Insumos",
    "description": "Saldo de inventario de insumos",
    "expression": "II = PI - UII",  # CORREGIDO
    "variable1": "II",
    "variable2": "PI",
    "variable3": "UII",
    "area": "Inventario Insumos"
  },

  {
    "name": "Inventario Productos Finales",
    "description": "Saldo de inventario de productos finales",
    "expression": "IPF = PPL - TPV",  # CORREGIDO
    "variable1": "IPF",
    "variable2": "PPL",
    "variable3": "TPV",
    "area": "Inventario Productos Finales"
  },

  {
    "name": "Rotación Inventario",
    "description": "Rotación de inventario",
    "expression": "RTI = CPROD / max(IPF, 1)",
    "variable1": "RTI",
    "variable2": "CPROD",
    "variable3": "IPF",
    "area": "Inventario Productos Finales" 
  },

  {
    "name": "Costo Unitario Inventario",
    "description": "Costo unitario del inventario",
    "expression": "CUI = TG / max(IPF, 1)",
    "variable1": "CUI",
    "variable2": "TG",
    "variable3": "IPF",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Almacenamiento",
    "description": "Costo de almacenamiento",
    "expression": "CA = IPF * (CUI / 1000)",  # Ajuste de escala
    "variable1": "CA",
    "variable2": "IPF",
    "variable3": "CUI",
    "area": "Inventario Productos Finales"
  },

  # DISTRIBUCIÓN
  {
    "name": "Costo Total Transporte",
    "description": "Costo total de transporte",
    "expression": "CTTL = CUTRANS * min(CTPLV, TPV)",  # Limitado a ventas
    "variable1": "CTTL",
    "variable2": "CUTRANS",  
    "variable3": "CTPLV",
    "area": "Distribución"
  },

  {
    "name": "Costo Total Reorden",
    "description": "Costo total de reorden de insumos",
    "expression": "CTR = CTAI + CUP",
    "variable1": "CTR",
    "variable2": "CTAI",
    "variable3": "CUP",
    "area": "Contabilidad"
  },

  # ABASTECIMIENTO
  {
    "name": "Tiempo Formulación Pedido",
    "description": "Tiempo para formular pedido",
    "expression": "DF = NPD * TMP",
    "variable1": "DF",
    "variable2": "NPD",  
    "variable3": "TMP",
    "area": "Abastecimiento"
  },

  {
    "name": "Nivel Ideal Inventario Leche",
    "description": "Nivel óptimo de inventario",
    "expression": "NIL = (CTL * DPL) + SI",
    "variable1": "NIL",
    "variable2": "CTL",
    "variable3": "DPL",
    "variable4": "SI",
    "area": "Abastecimiento" 
  },

  {
    "name": "Pedido Reabastecimiento Leche",
    "description": "Cantidad para reabastecer",
    "expression": "PRL = max(0, NIL - DE)",  # Evitar negativos
    "variable1": "PRL",
    "variable2": "NIL",
    "variable3": "DE",
    "area": "Abastecimiento"   
  },

  # MARKETING
  {
    "name": "Costo Unitario Adquisición Clientes",
    "expression": "CUAC = (GMM / 30) / max(CPD, 1)",  # GMM mensual a diario
    "variable1": "CUAC",
    "variable2": "GMM",
    "variable3": "CPD",
    "area": "Marketing"
  },

  {
    "name": "Rotación Clientes",
    "description": "Rotación de clientes",
    "expression": "RTC = TPV / max(TCA, 1)",
    "variable1": "RTC",
    "variable2": "TPV",
    "variable3": "TCA",
    "area": "Marketing"
  },

  # COMPETENCIA
  {
    "name": "Participación Mercado",
    "description": "Participación de mercado",
    "expression": "PM = TPV / max(DH, 1)",
    "variable1": "PM",
    "variable2": "TPV",
    "variable3": "DH",
    "area": "Competencia"
  },

  {
    "name": "Nivel de Competencia en el Mercado",
    "description": "Nivel de competencia basado en precios",
    "expression": "NCM = abs(PVP - PC) / max(PC, 1)",  # Diferencia relativa
    "variable1": "NCM",
    "variable2": "PVP",
    "variable3": "PC",
    "area": "Competencia"
  },

  # RECURSOS HUMANOS
  {
    "name": "Productividad Empleados",
    "description": "Productividad por empleado",
    "expression": "PE = TPV / max(NEPP, 1)",
    "variable1": "PE",
    "variable2": "TPV",
    "variable3": "NEPP",
    "area": "Recursos Humanos"
  },

  {
    "name": "Horas Ociosas",
    "description": "Horas ociosas en producción",
    "expression": "HO = max(0, (NMD * MLP) - (QPL * TPE))",
    "variable1": "HO",
    "variable2": "NMD",
    "variable3": "MLP",
    "variable4": "TPE",  
    "area": "Recursos Humanos" 
  },

  {
    "name": "Costo Horas Ociosas",
    "description": "Costo de las horas ociosas",
    "expression": "CHO = HO * (CPMO / 60)",  # CPMO por minuto
    "variable1": "CHO",
    "variable2": "HO",
    "variable3": "CPMO",
    "area": "Contabilidad"
  },

  # ECUACIÓN FINAL - Demanda Total
  {
    "name": "Demanda Total",
    "description": "Demanda total del sistema",
    "expression": "DT = TPV + DI",  # Simplificado
    "variable1": "DT",
    "variable2": "TPV",
    "variable3": "DI",
    "area": "Ventas"
  }
]