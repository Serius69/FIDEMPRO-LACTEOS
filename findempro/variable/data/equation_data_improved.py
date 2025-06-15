# equations_improved_dh.py - Sistema de ecuaciones mejorado basado en Demanda Histórica

equations_data_improved = [
  # NÚCLEO: CÁLCULO DE DEMANDA PROMEDIO
  {
    "name": "Demanda Promedio Histórica",
    "description": "Media de los datos históricos de demanda - Variable central del modelo",
    "expression": "DPH = mean(DH)",  # Media de los 30+ datos históricos
    "variable1": "DPH",
    "variable2": "DH",
    "area": "Análisis Demanda"
  },
  
  {
    "name": "Desviación Estándar Demanda",
    "description": "Variabilidad de la demanda para cálculos de seguridad",
    "expression": "DSD = std(DH)",
    "variable1": "DSD", 
    "variable2": "DH",
    "area": "Análisis Demanda"
  },

  {
    "name": "Coeficiente Variación Demanda",
    "description": "Medida de variabilidad relativa",
    "expression": "CVD = DSD / max(DPH, 1)",
    "variable1": "CVD",
    "variable2": "DSD",
    "variable3": "DPH",
    "area": "Análisis Demanda"
  },

  # VENTAS - Basadas en demanda promedio histórica
  {
    "name": "Demanda Diaria Proyectada",
    "description": "Demanda esperada basada en histórico y tendencia",
    "expression": "DDP = DPH * (1 + (DE - DPH) / max(DPH, 1) * 0.2) * ED",  # Ajuste gradual hacia DE
    "variable1": "DDP",
    "variable2": "DPH",
    "variable3": "DE",
    "variable4": "ED",
    "area": "Ventas"
  },

  {
    "name": "Total clientes atendidos en el dia",
    "description": "Clientes basados en demanda promedio y capacidad",
    "expression": "TCAE = min(CPD * (DDP / DPH), (DDP / max(VPC, 1)), CPD * 1.2)",  # Escalado por demanda
    "variable1": "TCAE",
    "variable2": "CPD",
    "variable3": "DDP",
    "variable4": "DPH",
    "variable5": "VPC",
    "area": "Ventas"
  },
  
  {
    "name": "Ventas por Cliente",
    "description": "Unidades promedio vendidas por cliente basadas en histórico",
    "expression": "VPC = DPH / max(CPD, 1) * (1 + 0.1 * (DDP / DPH - 1))",  # Base histórica con ajuste
    "variable1": "VPC",
    "variable2": "DPH",
    "variable3": "CPD",
    "variable4": "DDP",
    "area": "Ventas"
  },

  {
    "name": "Total Productos Vendidos",
    "description": "Ventas reales limitadas por inventario y demanda",
    "expression": "TPV = min(DDP, IPF + PPL, TCAE * VPC)",  # Limitado por demanda proyectada
    "variable1": "TPV",
    "variable2": "DDP",
    "variable3": "IPF",
    "variable4": "PPL",
    "variable5": "TCAE",
    "variable6": "VPC",
    "area": "Ventas"
  },

  {
    "name": "Demanda Insatisfecha",
    "description": "Demanda no cubierta",
    "expression": "DI = max(0, DDP - TPV)",
    "variable1": "DI",
    "variable2": "DDP",
    "variable3": "TPV",
    "area": "Ventas"
  },

  {
    "name": "Nivel Servicio al Cliente",
    "description": "Porcentaje de demanda satisfecha",
    "expression": "NSC = TPV / max(DDP, 1)",
    "variable1": "NSC",
    "variable2": "TPV",
    "variable3": "DDP",
    "area": "Ventas"
  },

  # PRODUCCIÓN - Basada en demanda histórica con buffer de seguridad
  {
    "name": "Producción Objetivo Diaria",
    "description": "Meta de producción basada en histórico y variabilidad",
    "expression": "POD = DPH + (DSD * 1.65) + max(0, (DDP - DPH) * 0.5)",  # Media + 1.65σ + ajuste tendencia
    "variable1": "POD",
    "variable2": "DPH",
    "variable3": "DSD",
    "variable4": "DDP",
    "area": "Producción"
  },

  {
    "name": "Capacidad de Producción Real",
    "description": "Capacidad efectiva considerando eficiencia",
    "expression": "CPROD = min(NEPP * (MLP / TPE) * CPPL * 0.85, CIP, POD * 1.2)",  # Limitada por objetivo
    "variable1": "CPROD",
    "variable2": "NEPP",
    "variable3": "MLP",
    "variable4": "TPE",
    "variable5": "CPPL",
    "variable6": "CIP",
    "variable7": "POD",
    "area": "Producción"
  },

  {
    "name": "Cantidad producida de productos lácteos",
    "description": "Producción real basada en demanda histórica y restricciones",
    "expression": "QPL = min(max(POD - IPF, DPH * 0.8), CPROD, (II / CINSP) * 0.95)",  # Mínimo 80% DPH
    "variable1": "QPL",
    "variable2": "POD",
    "variable3": "IPF",
    "variable4": "DPH",
    "variable5": "CPROD",
    "variable6": "II",
    "variable7": "CINSP",
    "area": "Producción"
  },

  {
    "name": "Productos Producidos por Lote",
    "description": "Producción diaria en lotes",
    "expression": "PPL = QPL",
    "variable1": "PPL",
    "variable2": "QPL",
    "area": "Producción"
  },

  {
    "name": "Total Productos Producidos",
    "description": "Acumulado de producción",
    "expression": "TPPRO = PPL",
    "variable1": "TPPRO",
    "variable2": "PPL",
    "area": "Producción"
  },

  {
    "name": "Factor Utilización",
    "description": "Utilización real vs capacidad",
    "expression": "FU = QPL / max(CPROD, 1)",
    "variable1": "FU",
    "variable2": "QPL",
    "variable3": "CPROD",
    "area": "Producción"
  },

  {
    "name": "Eficiencia Producción",
    "description": "Eficiencia respecto a demanda histórica",
    "expression": "EP = QPL / max(DPH * 1.1, 1)",  # Producción vs demanda+10%
    "variable1": "EP",
    "variable2": "QPL",
    "variable3": "DPH",
    "area": "Producción"
  },

  # INVENTARIOS - Dimensionados según demanda histórica
  {
    "name": "Inventario Objetivo Productos",
    "description": "Inventario óptimo basado en demanda y variabilidad",
    "expression": "IOP = DPH * DPL + DSD * sqrt(DPL) * 1.65",  # Stock ciclo + seguridad
    "variable1": "IOP",
    "variable2": "DPH",
    "variable3": "DPL",
    "variable4": "DSD",
    "area": "Inventario Productos Finales"
  },

  {
    "name": "Inventario Productos Finales",
    "description": "Balance de productos terminados",
    "expression": "IPF = max(0, min(IPF + PPL - TPV, CMIPF))",
    "variable1": "IPF",
    "variable2": "PPL",
    "variable3": "TPV",
    "variable4": "CMIPF",
    "area": "Inventario Productos Finales"
  },

  {
    "name": "Días Cobertura Inventario",
    "description": "Días que cubre el inventario actual",
    "expression": "DCI = IPF / max(DPH, 1)",
    "variable1": "DCI",
    "variable2": "IPF",
    "variable3": "DPH",
    "area": "Inventario Productos Finales"
  },

  {
    "name": "Rotación Inventario",
    "description": "Veces que rota el inventario basado en demanda histórica",
    "expression": "RTI = (DPH * 30) / max((IPF + IOP) / 2, 1)",  # Mensual con inventario promedio
    "variable1": "RTI",
    "variable2": "DPH",
    "variable3": "IPF",
    "variable4": "IOP",
    "area": "Inventario Productos Finales"
  },

  {
    "name": "Inventario Objetivo Insumos",
    "description": "Inventario óptimo de insumos basado en producción histórica",
    "expression": "IOI = (DPH * CINSP * (TR + DPL)) + (DSD * CINSP * sqrt(TR + DPL) * 1.65)",
    "variable1": "IOI",
    "variable2": "DPH",
    "variable3": "CINSP",
    "variable4": "TR",
    "variable5": "DPL",
    "variable6": "DSD",
    "area": "Inventario Insumos"
  },

  {
    "name": "Pedido Insumos",
    "description": "Pedido optimizado basado en consumo histórico",
    "expression": "PI = max(0, IOI - II + (DPH * CINSP * TR))",  # Objetivo - actual + consumo lead time
    "variable1": "PI",
    "variable2": "IOI",
    "variable3": "II",
    "variable4": "DPH",
    "variable5": "CINSP",
    "variable6": "TR",
    "area": "Inventario Insumos"
  },

  {
    "name": "Uso de Inventario Insumos",
    "description": "Consumo real de insumos",
    "expression": "UII = QPL * CINSP",
    "variable1": "UII",
    "variable2": "QPL",
    "variable3": "CINSP",
    "area": "Inventario Insumos"
  },

  {
    "name": "Inventario Insumos",
    "description": "Balance de insumos",
    "expression": "II = max(0, II + PI - UII)",
    "variable1": "II",
    "variable2": "PI",
    "variable3": "UII",
    "area": "Inventario Insumos"
  },

  # CONTABILIDAD - Costos e ingresos basados en operación real
  {
    "name": "Ingresos Totales",
    "description": "Ingresos por ventas reales",
    "expression": "IT = TPV * PVP",
    "variable1": "IT",
    "variable2": "TPV",
    "variable3": "PVP",
    "area": "Contabilidad"
  },

  {
    "name": "Ingresos Esperados",
    "description": "Ingresos basados en demanda histórica promedio",
    "expression": "IE = DPH * PVP",
    "variable1": "IE",
    "variable2": "DPH",
    "variable3": "PVP",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Total Adquisición Insumos",
    "description": "Costo de insumos con descuentos por volumen",
    "expression": "CTAI = UII * CUIP * (1 - 0.05 * (PI > DPH * CINSP * 3))",  # Descuento si pedido > 3 días
    "variable1": "CTAI",
    "variable2": "UII",
    "variable3": "CUIP",
    "variable4": "PI",
    "variable5": "DPH",
    "variable6": "CINSP",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Variable Unitario",
    "description": "Costo variable por unidad basado en escala",
    "expression": "CVU = CTAI / max(QPL, 1) * (1 + 0.1 * (1 - QPL / max(DPH, 1)))",  # Penalización si produce menos
    "variable1": "CVU",
    "variable2": "CTAI",
    "variable3": "QPL",
    "variable4": "DPH",
    "area": "Contabilidad"
  },

  {
    "name": "Gastos Operativos",
    "description": "Gastos operativos escalados por producción",
    "expression": "GO = CFD * (0.7 + 0.3 * (QPL / max(DPH, 1))) + (SE / 30) + CTAI",  # 70% fijo + 30% variable
    "variable1": "GO",
    "variable2": "CFD",
    "variable3": "QPL",
    "variable4": "DPH",
    "variable5": "SE",
    "variable6": "CTAI",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Total Transporte",
    "description": "Costo de distribución basado en ventas reales",
    "expression": "CTTL = ceil(TPV / CTPLV) * CUTRANS * 50 * (0.8 + 0.2 * (TPV / max(DPH, 1)))",  # Eficiencia por volumen
    "variable1": "CTTL",
    "variable2": "TPV",
    "variable3": "CTPLV",
    "variable4": "CUTRANS",
    "variable5": "DPH",
    "area": "Distribución"
  },

  {
    "name": "Costo Almacenamiento",
    "description": "Costo de mantener inventario con penalización por exceso",
    "expression": "CA = (IPF * PVP * 0.002) + 100 * (IPF > 0) + 50 * max(0, (IPF - DPH * 3) / DPH)",  # Penaliza exceso
    "variable1": "CA",
    "variable2": "IPF",
    "variable3": "PVP",
    "variable4": "DPH",
    "area": "Inventario Productos Finales"
  },

  {
    "name": "Merma Producción",
    "description": "Pérdida en proceso proporcional a producción",
    "expression": "MP = QPL * (0.015 + 0.005 * max(0, (QPL - DPH * 1.2) / DPH))",  # Mayor merma si sobreproducción
    "variable1": "MP",
    "variable2": "QPL",
    "variable3": "DPH",
    "area": "Control de Calidad"
  },

  {
    "name": "Merma Inventario",
    "description": "Pérdida por vencimientos",
    "expression": "MI = IPF * (0.005 + 0.01 * max(0, (IPF - DPH * 2) / DPH))",  # Aumenta si inventario alto
    "variable1": "MI",
    "variable2": "IPF",
    "variable3": "DPH",
    "area": "Inventario Productos Finales"
  },

  {
    "name": "Costo Total Mermas",
    "description": "Costo de pérdidas totales",
    "expression": "CTM = (MP + MI) * PVP * 0.7",
    "variable1": "CTM",
    "variable2": "MP",
    "variable3": "MI",
    "variable4": "PVP",
    "area": "Contabilidad"
  },

  {
    "name": "Gastos Generales",
    "description": "Gastos generales proporcionales a operación",
    "expression": "GG = (GMM / 30) * (TPV / max(DPH, 0.8)) + CTTL + CA + CTM",  # Marketing escalado por ventas
    "variable1": "GG",
    "variable2": "GMM",
    "variable3": "TPV",
    "variable4": "DPH",
    "variable5": "CTTL",
    "variable6": "CA",
    "variable7": "CTM",
    "area": "Contabilidad"
  },

  {
    "name": "Total Gastos",
    "description": "Total de gastos del día",
    "expression": "TG = GO + GG",
    "variable1": "TG",
    "variable2": "GO",
    "variable3": "GG",
    "area": "Contabilidad"
  },

  {
    "name": "Ganancias Totales",
    "description": "Utilidad neta del día",
    "expression": "GT = IT - TG",
    "variable1": "GT",
    "variable2": "IT",
    "variable3": "TG",
    "area": "Contabilidad"
  },

  {
    "name": "Ingreso Bruto",
    "description": "Margen bruto",
    "expression": "IB = IT - CTAI",
    "variable1": "IB",
    "variable2": "IT",
    "variable3": "CTAI",
    "area": "Contabilidad"
  },

  {
    "name": "Margen Bruto",
    "description": "Porcentaje de margen bruto",
    "expression": "MB = IB / max(IT, 1)",
    "variable1": "MB",
    "variable2": "IB",
    "variable3": "IT",
    "area": "Contabilidad"
  },

  {
    "name": "Nivel de Rentabilidad",
    "description": "Rentabilidad sobre ventas",
    "expression": "NR = GT / max(IT, 1)",
    "variable1": "NR",
    "variable2": "GT",
    "variable3": "IT",
    "area": "Contabilidad"
  },

  {
    "name": "Rentabilidad vs Esperada",
    "description": "Rentabilidad real vs esperada por demanda histórica",
    "expression": "RVE = GT / max(IE * MB, 1)",  # Ganancia real vs esperada
    "variable1": "RVE",
    "variable2": "GT",
    "variable3": "IE",
    "variable4": "MB",
    "area": "Contabilidad"
  },

  # COSTOS UNITARIOS - Basados en escala de producción
  {
    "name": "Costo Promedio Producción",
    "description": "Costo por unidad con economías de escala",
    "expression": "CPP = (CTAI + (SE/30) * (QPL/DPH) + CFD * (QPL/DPH)) / max(QPL, 1)",
    "variable1": "CPP",
    "variable2": "CTAI",
    "variable3": "SE",
    "variable4": "QPL",
    "variable5": "DPH",
    "variable6": "CFD",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Promedio Venta",
    "description": "Costo total por unidad vendida",
    "expression": "CPV = TG / max(TPV, 1)",
    "variable1": "CPV",
    "variable2": "TG",
    "variable3": "TPV",
    "area": "Contabilidad"
  },

  {
    "name": "Costo Unitario Producción",
    "description": "Costo unitario total de producción",
    "expression": "CUP = CPP * (1 + 0.1 * abs(QPL - DPH) / max(DPH, 1))",  # Penaliza desviación de óptimo
    "variable1": "CUP",
    "variable2": "CPP",
    "variable3": "QPL",
    "variable4": "DPH",
    "area": "Contabilidad"
  },

  {
    "name": "Precio Venta Recomendado",
    "description": "Precio óptimo basado en costos y demanda",
    "expression": "PVR = max(CUP * (1.3 + 0.05 * (1 - TPV/DPH)), PC * (0.95 + 0.05 * NSC))",  # Ajuste por servicio
    "variable1": "PVR",
    "variable2": "CUP",
    "variable3": "TPV",
    "variable4": "DPH",
    "variable5": "PC",
    "variable6": "NSC",
    "area": "Ventas"
  },

  # RECURSOS HUMANOS - Productividad basada en demanda
  {
    "name": "Productividad Empleados",
    "description": "Litros por empleado vs demanda histórica",
    "expression": "PE = QPL / max(NEPP, 1) / (DPH / max(NEPP, 1))",  # Productividad relativa
    "variable1": "PE",
    "variable2": "QPL",
    "variable3": "NEPP",
    "variable4": "DPH",
    "area": "Recursos Humanos"
  },

  {
    "name": "Horas Necesarias Producción",
    "description": "Horas requeridas para producción basada en demanda",
    "expression": "HNP = (DPH / CPPL) * TPE",
    "variable1": "HNP",
    "variable2": "DPH",
    "variable3": "CPPL",
    "variable4": "TPE",
    "area": "Recursos Humanos"
  },

  {
    "name": "Horas Ociosas",
    "description": "Tiempo no productivo",
    "expression": "HO = max(0, MLP - HNP * (QPL / max(DPH, 1)))",
    "variable1": "HO",
    "variable2": "MLP",
    "variable3": "HNP",
    "variable4": "QPL",
    "variable5": "DPH",
    "area": "Recursos Humanos"
  },

  {
    "name": "Costo Horas Ociosas",
    "description": "Costo del tiempo improductivo",
    "expression": "CHO = (HO / MLP) * (SE / 30) / NEPP",
    "variable1": "CHO",
    "variable2": "HO",
    "variable3": "MLP",
    "variable4": "SE",
    "variable5": "NEPP",
    "area": "Contabilidad"
  },

  # MARKETING Y CLIENTES - Efectividad basada en demanda
  {
    "name": "Efectividad Marketing",
    "description": "ROI de marketing basado en crecimiento vs histórico",
    "expression": "EM = max(0, (TPV - DPH) / max(DPH, 1)) / max((GMM / 30) / (DPH * PVP), 0.01)",
    "variable1": "EM",
    "variable2": "TPV",
    "variable3": "DPH",
    "variable4": "GMM",
    "variable5": "PVP",
    "area": "Marketing"
  },

  {
    "name": "Costo Unitario Adquisición Clientes",
    "description": "Costo por cliente nuevo considerando base histórica",
    "expression": "CUAC = (GMM / 30) / max((TCAE - (DPH / VPC)) * 0.5, 1)",  # Solo nuevos clientes
    "variable1": "CUAC",
    "variable2": "GMM",
    "variable3": "TCAE",
    "variable4": "DPH",
    "variable5": "VPC",
    "area": "Marketing"
  },

  {
    "name": "Frecuencia de Compra",
    "description": "Frecuencia real vs histórica",
    "expression": "FC = (TCAE / max(CPD, 1)) / (DPH / (max(CPD * VPC, 1)))",
    "variable1": "FC",
    "variable2": "TCAE",
    "variable3": "CPD",
    "variable4": "DPH",
    "variable5": "VPC",
    "area": "Ventas"
  },

  # COMPETENCIA Y MERCADO
  {
    "name": "Participación Mercado",
    "description": "Share basado en demanda histórica del mercado",
    "expression": "PM = TPV / max(DH * 10, 1)",  # Asume mercado 10x mayor
    "variable1": "PM",
    "variable2": "TPV",
    "variable3": "DH",
    "area": "Competencia"
  },

  {
    "name": "Índice Competitividad",
    "description": "Competitividad multifactorial",
    "expression": "IC = (0.3 * (1 - abs(PVP - PC) / PC)) + (0.4 * NSC) + (0.3 * (TPV / DPH))",
    "variable1": "IC",
    "variable2": "PVP",
    "variable3": "PC",
    "variable4": "NSC",
    "variable5": "TPV",
    "variable6": "DPH",
    "area": "Competencia"
  },

  # INDICADORES CLAVE DE DESEMPEÑO
  {
    "name": "Demanda Total",
    "description": "Demanda total del período",
    "expression": "DT = DDP",
    "variable1": "DT",
    "variable2": "DDP",
    "area": "Ventas"
  },

  {
    "name": "Eficiencia Operativa Global",
    "description": "OEE basado en demanda histórica",
    "expression": "EOG = (QPL / max(DPH * 1.2, 1)) * (1 - (MP + MI) / QPL) * NSC",
    "variable1": "EOG",
    "variable2": "QPL",
    "variable3": "DPH",
    "variable4": "MP",
    "variable5": "MI",
    "variable6": "NSC",
    "area": "Producción"
  },

  {
    "name": "Índice Satisfacción Cliente",
    "description": "Satisfacción basada en servicio y precio",
    "expression": "ISC = (0.5 * NSC) + (0.3 * (PC / PVP)) + (0.2 * (1 - DI / max(DDP, 1)))",
    "variable1": "ISC",
    "variable2": "NSC",
    "variable3": "PC",
    "variable4": "PVP",
    "variable5": "DI",
    "variable6": "DDP",
    "area": "Ventas"
  },

  {
    "name": "Punto de Equilibrio Diario",
    "description": "Ventas mínimas basadas en estructura de costos histórica",
    "expression": "PED = (CFD + (SE / 30) + (GMM / 30) * (DPH / max(DPH, 1))) / max(PVP - CVU, 1)",
    "variable1": "PED",
    "variable2": "CFD",
    "variable3": "SE",
    "variable4": "GMM",
    "variable5": "DPH",
    "variable6": "PVP",
    "variable7": "CVU",
    "area": "Contabilidad"
  },

  {
    "name": "Retorno Inversión",
    "description": "ROI ajustado por desempeño vs histórico",
    "expression": "RI = (GT / max(abs(TG), 1)) * (TPV / max(DPH, 1)) * NSC",
    "variable1": "RI",
    "variable2": "GT",
    "variable3": "TG",
    "variable4": "TPV",
    "variable5": "DPH",
    "variable6": "NSC",
    "area": "Contabilidad"
  },

  {
    "name": "Índice Desempeño Global",
    "description": "KPI integral basado en demanda histórica",
    "expression": "IDG = (0.3 * (TPV/DPH)) + (0.2 * EOG) + (0.2 * ISC) + (0.3 * (GT/max(IE*0.15,1)))",
    "variable1": "IDG",
    "variable2": "TPV",
    "variable3": "DPH",
    "variable4": "EOG",
    "variable5": "ISC",
    "variable6": "GT",
    "variable7": "IE",
    "area": "Indicadores Generales"
  }
]


# FUNCIONES AUXILIARES PARA EL CÁLCULO
def calculate_dph(historical_demand):
    """Calcula la demanda promedio histórica"""
    if isinstance(historical_demand, list) and len(historical_demand) >= 30:
        return sum(historical_demand) / len(historical_demand)
    return 2500  # Valor por defecto si no hay datos suficientes

def calculate_dsd(historical_demand):
    """Calcula la desviación estándar de la demanda"""
    if isinstance(historical_demand, list) and len(historical_demand) >= 30:
        mean = calculate_dph(historical_demand)
        variance = sum((x - mean) ** 2 for x in historical_demand) / len(historical_demand)
        return variance ** 0.5
    return 250  # Valor por defecto (10% de la media default)

# EJEMPLO DE USO EN SIMULACIÓN
def simulate_day_with_historical_demand(variables, historical_demand):
    """
    Simula un día de operación basándose en la demanda histórica
    """
    # Calcular variables base de demanda histórica
    variables['DPH'] = calculate_dph(historical_demand)
    variables['DSD'] = calculate_dsd(historical_demand)
    variables['CVD'] = variables['DSD'] / max(variables['DPH'], 1)
    
    # Proyectar demanda del día
    variables['DDP'] = variables['DPH'] * (1 + (variables['DE'] - variables['DPH']) / max(variables['DPH'], 1) * 0.2) * variables['ED']
    
    # Calcular producción objetivo
    variables['POD'] = variables['DPH'] + (variables['DSD'] * 1.65) + max(0, (variables['DDP'] - variables['DPH']) * 0.5)
    
    # El resto de las variables se calculan en cascada según las ecuaciones
    
    return variables

# VALIDACIÓN DEL MODELO
validation_metrics = {
    "coherencia_demanda_produccion": {
        "descripcion": "Producción debe estar entre 80% y 120% de demanda promedio",
        "formula": "0.8 <= QPL/DPH <= 1.2",
        "peso": 0.25
    },
    "nivel_servicio_minimo": {
        "descripcion": "Nivel de servicio debe ser superior al 90%",
        "formula": "NSC >= 0.9",
        "peso": 0.20
    },
    "rentabilidad_positiva": {
        "descripcion": "Rentabilidad debe ser positiva en operación normal",
        "formula": "NR > 0 cuando TPV >= 0.8 * DPH",
        "peso": 0.20
    },
    "inventario_equilibrado": {
        "descripcion": "Inventario entre 1 y 5 días de cobertura",
        "formula": "1 <= DCI <= 5",
        "peso": 0.15
    },
    "costos_coherentes": {
        "descripcion": "Costos variables deben ser menores al 70% del precio",
        "formula": "CVU <= 0.7 * PVP",
        "peso": 0.20
    }
}