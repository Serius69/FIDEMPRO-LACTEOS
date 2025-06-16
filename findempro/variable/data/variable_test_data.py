
  
  
  # variables_data.py - Versión Final con valores default
variables_data = [
  
  
  
  
  {
    'name': 'Ventas por Cliente Base',
    'initials': 'VPC_BASE',
    'type': 3,
    'unit': 'L',
    'description': 'Ventas por cliente sin ajustes',
    'default_value': 30
},

{
    'name': 'Inventario Productos Finales Inicial',
    'initials': 'IPF_INICIAL',
    'type': 2,
    'unit': 'L',
    'description': 'Inventario al inicio del día',
    'default_value': 1000
},

{
    'name': 'Inventario Insumos Inicial',
    'initials': 'II_INICIAL',
    'type': 2,
    'unit': 'L',
    'description': 'Inventario de insumos al inicio del día',
    'default_value': 5000
},

{
    'name': 'Inventario Productos Finales Nuevo',
    'initials': 'IPF_NEW',
    'type': 3,
    'unit': 'L',
    'description': 'Inventario calculado antes de actualizar',
    'default_value': 1000
},
  
{
    'name': 'Distancia Promedio de Entrega',
    'initials': 'DPE',
    'type': 1,
    'unit': 'KM',
    'description': 'Distancia promedio a clientes',
    'default_value': 50
},
  
# VARIABLES EXÓGENAS (TIPO 1) - Variables de entrada del sistema
{'name': 'PRECIO DE VENTA DEL PRODUCTO',
'initials': 'PVP',
'type': 1,
'unit': 'BS',
'description': 'PRECIO DE VENTA DEL PRODUCTO LÁCTEO',
'default_value': 15.50},

{'name': 'DEMANDA HISTÓRICA',
'initials': 'DH',
'type': 1,
'unit': 'L',
'description': 'DATOS HISTÓRICOS DE DEMANDA DE LOS ÚLTIMOS UNIDADES DE TIEMPO',
'default_value': 2500},

{'name': 'DEMANDA ESPERADA',
'initials': 'DE',
'type': 1,
'unit': 'L',
'description': 'DEMANDA ESPERADA EN EL PERIODO DE TIEMPO ESTABLECIDO',
'default_value': 2650},

{
    'name': 'CAPACIDAD INVENTARIO PRODUCTOS',
    'initials': 'CIP',
    'type': 1,
    'unit': 'L',
    'description': 'CAPACIDAD MÁXIMA QUE LA EMPRESA PUEDE ALMACENAR EN INVENTARIO',
    'default_value': 10000  # CAMBIAR de 15000 a 10000 - más realista
},

{'name': 'ESTACIONALIDAD DE LA DEMANDA',
'initials': 'ED',
'type': 1,
'unit': '[0-1]',
'description': 'VARIACIONES PREDECIBLES DE LA DEMANDA',
'default_value': 1.0},

{
    'name': 'COSTO UNITARIO INSUMO PRODUCCIÓN',
    'initials': 'CUIP',
    'type': 1,
    'unit': 'BS/L',
    'description': 'COSTO QUE LE CUESTA A LA EMPRESA POR INSUMO',
    'default_value': 7.50  # CAMBIAR de 8.20 a 7.50 para margen más realista
},

{"name": "Tiempo Promedio entre Compras",
"initials": "TPC",
'type': 1,
"unit": "DÍAS",
"description": "Tiempo promedio que transcurre entre las compras de los clientes",
"default_value": 2},

{'name': 'CLIENTES POR DÍA',
'initials': 'CPD',
'type': 1,
'unit': 'CLIENTES',
'description': 'NÚMERO DE CLIENTES ATENDIDOS POR DÍA',
'default_value': 85},

{'name': 'NUMERO DE EMPLEADOS',
'initials': 'NEPP',
'type': 1,
'unit': 'EMPLEADOS',
'description': 'Numero de empleados',
'default_value': 15},

{'name': 'Cantidad Promedio Producción por Lote',
'initials': 'CPPL',
'type': 1,
'unit': 'L',
'description': 'Cantidad Promedio Producción por Lote',
'default_value': 500},

{
    'name': 'Tiempo de produccion por empleado',
    'initials': 'TPE',
    'type': 1,
    'unit': 'minutos',
    'description': 'Tiempo de produccion por empleado',
    'default_value': 30  # CAMBIAR de 45 a 30 - más productivo
},

{
    'name': 'SUELDOS EMPLEADOS',
    'initials': 'SE',
    'type': 1,
    'unit': 'BS/MES',
    'description': 'SUELDOS EMPLEADOS MENSUAL',
    'default_value': 45000  # CAMBIAR de 48000 a 45000
},

{'name': 'PRECIO DE VENTA DE LA COMPETENCIA',
'initials': 'PC',
'type': 1,
'unit': 'BS',
'description': 'PRECIO DE VENTA DEL MISMO PRODUCTO PERO DE LA COMPETENCIA',
'default_value': 15.80},

{
    'name': 'COSTO FIJO DIARIO',
    'initials': 'CFD',
    'type': 1,
    'unit': 'BS/DÍA',
    'description': 'COSTO FIJO DIARIO DE LA EMPRESA',
    'default_value': 1500  # CAMBIAR de 1800 a 1500 para mejorar rentabilidad
},

{
    'name': 'COSTO UNITARIO POR TRANSPORTE',
    'initials': 'CUTRANS',
    'type': 1,
    'unit': 'BS/L',
    'description': 'COSTO UNITARIO POR TRANSPORTE',
    'default_value': 0.25  # CAMBIAR de 0.35 a 0.25 - reducir costos
},

{'name': 'Tiempo Medio Procesamiento Pedido',
'initials': 'TMP',
'type': 1,
'unit': 'DIAS',
'description': 'TIEMPO MEDIO DE PROCESAMIENTO DE PEDIDOS',
'default_value': 1},

{
    'name': 'Cantidad transportada por viaje',
    'initials': 'CTPLV',
    'type': 1,
    'unit': 'L',
    'description': 'Cantidad transportada por viaje',
    'default_value': 2000  # CAMBIAR de 1500 a 2000 - más eficiente
},

{'name': 'cantidad promedio producida por lote',
'initials': 'CPL',
'type': 1,
'unit': 'L',
'description': 'cantidad promedio producida por lote',
'default_value': 2500},

{
    'name': 'GASTO TOTAL MARKETING',
    'initials': 'GMM',
    'type': 1,
    'unit': 'BS/MES',
    'description': 'GASTO EN MARKETING MENSUAL',
    'default_value': 3000  # CAMBIAR de 3500 a 3000
},

{'name': 'TIEMPO REABASTECIMIENTO',
'initials': 'TR',
'type': 1,
'unit': 'DIAS',
'description': 'PERIODO NECESARIO PARA REPONER EL INVENTARIO',
'default_value': 3},

{
    'name': 'CANTIDAD DE INSUMOS PARA UN PRODUCTO',
    'initials': 'CINSP',
    'type': 1,
    'unit': 'L',
    'description': 'CANTIDAD DE INSUMOS POR PRODUCTO',
    'default_value': 1.02  # CAMBIAR de 1.05 a 1.02 - menos desperdicio
},

{'name': 'CAPACIDAD MÁXIMA INVENTARIO PRODUCTO FINAL',
'initials': 'CMIPF',
'type': 1,
'unit': 'L',
'description': 'CAPACIDAD MAXIMA DE INVENTARIO PRODUCTO FINAL',
'default_value': 20000},

{'name': 'NUMERO MAXIMO DE DIAS',
'initials': 'NMD',
'type': 1,
'unit': 'DIAS',
'description': 'NUMERO DE DIAS DE SIMULACION',
'default_value': 30},

{'name': 'Número de Proveedores de Leche',
'initials': 'NPD',
'type': 1,
'unit': 'PROVEEDORES',
'description': 'Número de Proveedores de Leche',
'default_value': 3},

{
    'name': 'Stock de Inventario mínimo de Seguridad',
    'initials': 'SI',
    'type': 1,
    'unit': 'L',
    'description': 'Stock de Inventario mínimo de Seguridad',
    'default_value': 500  # CAMBIAR de 3000 a 500 - más proporcionado
},

{'name': 'Días Promedio de Reposición de Leche',
'initials': 'DPL',
'type': 1,
'unit': 'DIAS',
'description': 'Días Promedio de Reposición de Leche',
'default_value': 3},

{'name': 'Consumo diario promedio',
'initials': 'CTL',
'type': 1,
'unit': 'L',
'description': 'Consumo diario promedio',
'default_value': 2800},

{'name': 'Minutos Laborables Por Día',
'initials': 'MLP',
'type': 1,
'unit': 'MINUTOS',
'description': 'Minutos laborables por día (8 horas)',
'default_value': 480},

# VARIABLES DE ESTADO (TIPO 2) - Variables que cambian durante la simulación
{'name': 'Cantidad producida de productos lácteos',
'initials': 'QPL',
'type': 2,
'unit': 'L',
'description': 'Cantidad producida de productos lácteos',
'default_value': 2500},

{'name': 'CAPACIDAD DE PRODUCCIÓN',
'initials': 'CPROD',
'type': 2,
'unit': 'L/DIA',
'description': 'Capacidad de produccion diaria',
'default_value': 3000},

{'name': 'VENTAS POR CLIENTE',
'initials': 'VPC',
'type': 2,
'unit': 'L',
'description': 'CANTIDAD PROMEDIO DE VENTA POR CLIENTE',
'default_value': 30},

{'name': 'TOTAL CLIENTES ATENDIDOS EN EL DIA',
'initials': 'TCAE',
'type': 2,
'unit': 'CLIENTES',
'description': 'NÚMERO TOTAL DE CLIENTES QUE FUERON ATENDIDOS',
'default_value': 85},

{
    'name': 'INVENTARIO INSUMOS',
    'initials': 'II',
    'type': 2,
    'unit': 'L',
    'description': 'CANTIDAD DE INSUMOS EXISTENTES EN INVENTARIO',
    'default_value': 8000  # CAMBIAR de 5000 a 8000 - mejor cobertura
},

{
    'name': 'INVENTARIO PRODUCTOS FINALES',
    'initials': 'IPF',
    'type': 2,
    'unit': 'L',
    'description': 'CANTIDAD DE PRODUCTOS FINALES EN INVENTARIO',
    'default_value': 800  # CAMBIAR de 1000 a 800
},

{'name': 'PEDIDO INSUMOS',
'initials': 'PI',
'type': 2,
'unit': 'L',
'description': 'CANTIDAD DE INSUMOS A PEDIR',
'default_value': 3000},

{'name': 'USO DE INVENTARIO INSUMOS',
'initials': 'UII',
'type': 2,
'unit': 'L',
'description': 'CANTIDAD DE INSUMOS USADOS',
'default_value': 2500},

{'name': 'PRODUCTOS PRODUCIDOS POR LOTE',
'initials': 'PPL',
'type': 2,
'unit': 'L',
'description': 'CANTIDAD TOTAL DE PRODUCTOS LÁCTEOS POR LOTE',
'default_value': 500},

# VARIABLES ENDÓGENAS (TIPO 3) - Variables calculadas
{'name': 'COSTO TOTAL REORDEN',
'initials': 'CTR',
'type': 3,
'unit': 'BS',
'description': 'COSTO TOTAL DE REALIZAR UN NUEVO PEDIDO',
'default_value': 0},

{'name': 'COSTO TOTAL ADQUISICIÓN INSUMOS',
'initials': 'CTAI',
'type': 3,
'unit': 'BS',
'description': 'GASTO TOTAL EN LA ADQUISICIÓN DE INSUMOS',
'default_value': 0},

{'name': 'TOTAL PRODUCTOS VENDIDOS',
'initials': 'TPV',
'type': 3,
'unit': 'L',
'description': 'CANTIDAD TOTAL DE PRODUCTOS VENDIDOS',
'default_value': 0},

{'name': 'TOTAL PRODUCTOS PRODUCIDOS',
'initials': 'TPPRO',
'type': 3,
'unit': 'L',
'description': 'CANTIDAD TOTAL DE PRODUCTOS PRODUCIDOS',
'default_value': 0},

{'name': 'DEMANDA INSATISFECHA',
'initials': 'DI',
'type': 3,
'unit': 'L',
'description': 'CANTIDAD DE PRODUCTOS NO DISPONIBLES PARA VENTA',
'default_value': 0},

{'name': 'INGRESOS TOTALES',
'initials': 'IT',
'type': 3,
'unit': 'BS',
'description': 'CANTIDAD TOTAL DE INGRESOS GENERADOS',
'default_value': 0},

{'name': 'GANANCIAS TOTALES',
'initials': 'GT',
'type': 3,
'unit': 'BS',
'description': 'MONTO TOTAL DE GANANCIAS GENERADAS',
'default_value': 0},

{
    'name': 'TOTAL CLIENTES ATENDIDOS',
    'initials': 'TCA',
    'type': 2,  # Estado
    'unit': 'CLIENTES',
    'description': 'TOTAL DE CLIENTES EN EL PERÍODO',
    'default_value': 0  # AGREGAR
},

{'name': 'NIVEL DE RENTABILIDAD',
'initials': 'NR',
'type': 3,
'unit': '%',
'description': 'NIVEL DE RENTABILIDAD DE LA EMPRESA',
'default_value': 0},

{'name': 'GASTOS OPERATIVOS',
'initials': 'GO',
'type': 3,
'unit': 'BS',
'description': 'COSTOS NECESARIOS PARA EL FUNCIONAMIENTO DIARIO',
'default_value': 0},

{'name': 'GASTOS GENERALES',
'initials': 'GG',
'type': 3,
'unit': 'BS',
'description': 'COSTOS OPERATIVOS Y ADMINISTRATIVOS',
'default_value': 0},

{'name': 'COSTO TOTAL TRANSPORTE',
'initials': 'CTTL',
'type': 3,
'unit': 'BS',
'description': 'COSTOS TOTALES EN EL TRANSPORTE',
'default_value': 0},

{'name': 'COSTO PROMEDIO PRODUCCION',
'initials': 'CPP',
'type': 3,
'unit': 'BS',
'description': 'COSTOS PROMEDIO DE PRODUCCION POR PRODUCTO',
'default_value': 0},

{'name': 'COSTO PROMEDIO VENTA',
'initials': 'CPV',
'type': 3,
'unit': 'BS',
'description': 'COSTOS PROMEDIO DE VENTA POR PRODUCTO',
'default_value': 0},

{'name': 'COSTO PROMEDIO INSUMOS',
'initials': 'CPI',
'type': 3,
'unit': 'BS',
'description': 'COSTOS PROMEDIO DE INSUMOS',
'default_value': 0},

{'name': 'Costo Promedio Mano Obra',
'initials': 'CPMO',
'type': 3,
'unit': 'BS',
'description': 'COSTOS PROMEDIO DE MANO DE OBRA',
'default_value': 0},

{'name': 'Costo Unitario Producción',
'initials': 'CUP',
'type': 3,
'unit': 'BS',
'description': 'Costo Unitario Producción',
'default_value': 0},

{'name': 'Precio Venta Recomendado',
'initials': 'PVR',
'type': 3,
'unit': 'BS',
'description': 'Precio Venta Recomendado',
'default_value': 0},

{'name': 'Factor Utilización',
'initials': 'FU',
'type': 3,
'unit': '%',
'description': 'Factor Utilización',
'default_value': 0},

{'name': 'Total Gastos',
'initials': 'TG',
'type': 3,
'unit': 'BS',
'description': 'Total Gastos',
'default_value': 0},

{'name': 'Ingreso Bruto',
'initials': 'IB',
'type': 3,
'unit': 'BS',
'description': 'Ingreso Bruto',
'default_value': 0},

{'name': 'Margen Bruto',
'initials': 'MB',
'type': 3,
'unit': '%',
'description': 'Margen Bruto - Diferencia entre ingresos y costos directos',
'default_value': 0},

{'name': 'Retorno Inversión',
'initials': 'RI',
'type': 3,
'unit': '%',
'description': 'Retorno Inversión',
'default_value': 0},

{'name': 'Rotación Inventario',
'initials': 'RTI',
'type': 3,
'unit': 'VECES',
'description': 'Rotación Inventario',
'default_value': 0},

{'name': 'Rotación Clientes',
'initials': 'RTC',
'type': 3,
'unit': 'VECES',
'description': 'Frecuencia de compras de clientes',
'default_value': 0},

{'name': 'Participación Mercado',
'initials': 'PM',
'type': 3,
'unit': '%',
'description': 'Porcentaje de ventas en relación al mercado total',
'default_value': 0},

{'name': 'Productividad Empleados',
'initials': 'PE',
'type': 3,
'unit': 'L/EMPLEADO',
'description': 'Productividad de empleados',
'default_value': 0},

{'name': 'Horas Ociosas',
'initials': 'HO',
'type': 3,
'unit': 'MINUTOS',
'description': 'Tiempo sin actividad productiva',
'default_value': 0},

{'name': 'Costo Horas Ociosas',
'initials': 'CHO',
'type': 3,
'unit': 'BS',
'description': 'Costo del tiempo sin actividad productiva',
'default_value': 0},

{'name': 'Costo Almacenamiento',
'initials': 'CA',
'type': 3,
'unit': 'BS',
'description': 'Costo de almacenamiento de productos',
'default_value': 0},

{'name': 'Demanda Total',
'initials': 'DT',
'type': 3,
'unit': 'L',
'description': 'Demanda Total',
'default_value': 0},

{
    'name': 'NIVEL DE COMPETENCIA EN EL MERCADO',
    'initials': 'NCM',
    'type': 3,
    'unit': '%',
    'description': 'NIVEL DE COMPETENCIA EN EL MERCADO',
    'default_value': 0.5  # AGREGAR
},

{
    'name': 'FRECUENCIA DE COMPRA',
    'initials': 'FC',
    'type': 3,
    'unit': 'VECES/DÍA',
    'description': 'FRECUENCIA DE COMPRA DE CLIENTES',
    'default_value': 1.0  # AGREGAR
},

{'name': 'COSTO UNITARIO DE ADQUISICIÓN DE CLIENTES',
'initials': 'CUAC',
'type': 3,
'unit': 'BS/CLIENTE',
'description': 'GASTO PROMEDIO PARA CONSEGUIR UN CLIENTE',
'default_value': 0},

{'name': 'COSTO UNITARIO INVENTARIO',
'initials': 'CUI',
'type': 3,
'unit': 'BS',
'description': 'COSTO POR UNIDAD DE MANTENER INVENTARIO',
'default_value': 0},

{'name': 'Nivel Ideal del Inventario Leche',
'initials': 'NIL',
'type': 3,
'unit': 'L',
'description': 'NIVEL ÓPTIMO DE INVENTARIO',
'default_value': 0},

{'name': 'Tiempo Formulación Pedido',
'initials': 'DF',
'type': 3,
'unit': 'DIAS',
'description': 'Tiempo Formulación Pedido',
'default_value': 0},

{'name': 'Pedido Reabastecimiento Leche',
'initials': 'PRL',
'type': 3,
'unit': 'L',
'description': 'CANTIDAD PARA REABASTECER',
'default_value': 0},

{
    'name': 'Demanda Promedio Histórica',
    'initials': 'DPH',
    'type': 3,  # Calculada
    'unit': 'L/día',
    'description': 'Media de los datos históricos de demanda',
    'default_value': 0
  },
  {
    'name': 'Desviación Estándar Demanda',
    'initials': 'DSD',
    'type': 3,
    'unit': 'L',
    'description': 'Variabilidad de la demanda histórica',
    'default_value': 375  # CAMBIAR de 250 a 375 (15% de 2500)
},
  {
    'name': 'Coeficiente Variación Demanda',
    'initials': 'CVD',
    'type': 3,
    'unit': '%',
    'description': 'Variabilidad relativa de la demanda',
    'default_value': 0.1
},
  {
    'name': 'Demanda Diaria Proyectada',
    'initials': 'DDP',
    'type': 3,
    'unit': 'L/día',
    'description': 'Demanda esperada para el día actual',
    'default_value': 2500  # CAMBIAR de 2650 a 2500
},
  {
    'name': 'Nivel Servicio al Cliente',
    'initials': 'NSC',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje de demanda satisfecha',
    'default_value': 0.95
},
  {
    'name': 'Producción Objetivo Diaria',
    'initials': 'POD',
    'type': 3,
    'unit': 'L',
    'description': 'Meta de producción basada en histórico',
    'default_value': 2600  # CAMBIAR de 2800 a 2600
},

  {
    'name': 'Eficiencia Producción',
    'initials': 'EP',
    'type': 3,
    'unit': '%',
    'description': 'Eficiencia respecto a demanda histórica',
    'default_value': 0.85
},
  {
    'name': 'Inventario Objetivo Productos',
    'initials': 'IOP',
    'type': 3,
    'unit': 'L',
    'description': 'Inventario óptimo de productos terminados',
    'default_value': 2000  # CAMBIAR de 3000 a 2000
},
  {
    'name': 'Días Cobertura Inventario',
    'initials': 'DCI',
    'type': 3,
    'unit': 'días',
    'description': 'Días que cubre el inventario actual',
    'default_value': 2
},
  {
    'name': 'Inventario Objetivo Insumos',
    'initials': 'IOI',
    'type': 3,
    'unit': 'L',
    'description': 'Inventario óptimo de materias primas',
    'default_value': 5000
},
  {
    'name': 'Ingresos Esperados',
    'initials': 'IE',
    'type': 3,
    'unit': 'Bs',
    'description': 'Ingresos basados en demanda histórica',
    'default_value': 38750  # CAMBIAR a 2500 * 15.50
},
  {
    'name': 'Costo Variable Unitario',
    'initials': 'CVU',
    'type': 3,
    'unit': 'Bs/L',
    'description': 'Costo variable por unidad producida',
    'default_value': 7.65  # CAMBIAR a 7.50 * 1.02
},
  {
    'name': 'Rentabilidad vs Esperada',
    'initials': 'RVE',
    'type': 3,
    'unit': '%',
    'description': 'Rentabilidad real vs esperada',
    'default_value': 1.0
},
  {
    'name': 'Horas Necesarias Producción',
    'initials': 'HNP',
    'type': 3,
    'unit': 'minutos',
    'description': 'Horas requeridas según demanda',
    'default_value': 318  # (2650/500) * 60
},
  {
    'name': 'Efectividad Marketing',
    'initials': 'EM',
    'type': 3,
    'unit': 'ratio',
    'description': 'ROI de inversión en marketing',
    'default_value': 1.0
},
  {
    'name': 'Índice Competitividad',
    'initials': 'IC',
    'type': 3,
    'unit': '%',
    'description': 'Posición competitiva en el mercado',
    'default_value': 0.7
},
  {
    'name': 'Índice Desempeño Global',
    'initials': 'IDG',
    'type': 3,
    'unit': '%',
    'description': 'KPI integral de desempeño empresarial',
    'default_value': 0.75
},

{
    "name": "Merma Producción",
    "initials": "MP",
    "type": 3,
    "unit": "L",
    "description": "Pérdida en el proceso de producción",
    "default_value": 37.5  # 1.5% de 2500
},
  {
    "name": "Merma Inventario",
    "initials": "MI",
    "type": 3,
    "unit": "L",
    "description": "Pérdida en inventario por deterioro o vencimiento",
    "default_value": 5  # 0.5% de 1000
},
  {
    "name": "Costo Total Mermas",
    "initials": "CTM",
    "type": 3,
    "unit": "Bs",
    "description": "Costo monetario total de las mermas en producción e inventario",
    "default_value": 460  # (37.5 + 5) * 15.50 * 0.7
},
  {
    "name": "Eficiencia Operativa Global",
    "initials": "EOG",
    "type": 3,
    "unit": "%",
    "description": "Índice de eficiencia general de las operaciones",
    "default_value": 0.85
},
  {
    "name": "Índice Satisfacción Cliente",
    "initials": "ISC",
    "type": 3,
    "unit": "%",
    "description": "Medición del nivel de satisfacción de los clientes",
    "default_value": 0.9
},
  {
    'name': 'Punto de Equilibrio Diario',
    'initials': 'PED',
    'type': 3,
    'unit': 'L',
    'description': 'Punto de equilibrio financiero calculado diariamente',
    'default_value': 1800  # CAMBIAR de 2000 a 1800
}


]