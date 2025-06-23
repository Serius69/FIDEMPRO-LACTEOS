# variables_data_corrected.py - Versión Final Corregida sin errores

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
{
        'name': 'Precio de Venta del Producto (Default)',
        'initials': 'PVP',
        'type': 1,  # Exógena
        'unit': 'Bs',
        'description': 'Precio de venta del producto lácteo por litro',
        'default_value': 15.50  # VALOR CRÍTICO
    },

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
        'name': 'Costo Unitario Insumo',
        'initials': 'CUIP',
        'type': 1,
        'unit': 'Bs/L',
        'description': 'Costo unitario de insumos por litro',
        'default_value': 7.50  # Reducido de 8.20 para mejor margen
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
        'name': 'Sueldos Empleados',
        'initials': 'SE',
        'type': 1,
        'unit': 'Bs/mes',
        'description': 'Sueldos mensuales de empleados',
        'default_value': 45000  # Reducido de 48000
    },

{'name': 'PRECIO DE VENTA DE LA COMPETENCIA',
'initials': 'PC',
'type': 1,
'unit': 'BS',
'description': 'PRECIO DE VENTA DEL MISMO PRODUCTO PERO DE LA COMPETENCIA',
'default_value': 15.80},

{
        'name': 'Costo Fijo Diario',
        'initials': 'CFD',
        'type': 1,
        'unit': 'Bs/día',
        'description': 'Costos fijos diarios de operación',
        'default_value': 1500  # Reducido de 1800 para mejor rentabilidad
    },

{
        'name': 'Costo Transporte Unitario',
        'initials': 'CUTRANS',
        'type': 1,
        'unit': 'Bs/L',
        'description': 'Costo de transporte por litro',
        'default_value': 0.25  # Reducido de 0.35
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

{
        'name': 'Gastos Marketing Mensual',
        'initials': 'GMM',
        'type': 1,
        'unit': 'Bs/mes',
        'description': 'Gastos mensuales en marketing',
        'default_value': 3000  # Reducido de 3500
    },

{'name': 'TIEMPO REABASTECIMIENTO',
'initials': 'TR',
'type': 1,
'unit': 'DIAS',
'description': 'PERIODO NECESARIO PARA REPONER EL INVENTARIO',
'default_value': 3},

{
        'name': 'Conversión Insumos',
        'initials': 'CINSP',
        'type': 1,
        'unit': 'L/L',
        'description': 'Litros de insumo necesarios por litro de producto',
        'default_value': 1.02  # Reducido de 1.05 para menor desperdicio
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
        'name': 'Stock Inventario Seguridad',
        'initials': 'SI',
        'type': 1,
        'unit': 'L',
        'description': 'Stock mínimo de seguridad',
        'default_value': 500  # Aumentado de 100
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

{
    'name': 'Horas Totales de Operación',
    'initials': 'HTO',
    'type': 1,
    'unit': 'HORAS',
    'description': 'Horas totales programadas de operación por día',
    'default_value': 24
},

{
    'name': 'Cantidad Máxima Producible',
    'initials': 'QMAX',
    'type': 1,
    'unit': 'L',
    'description': 'Capacidad máxima teórica de producción diaria',
    'default_value': 3000
},

{
    'name': 'Temperatura Cadena Frío Objetivo',
    'initials': 'TCFO',
    'type': 1,
    'unit': '°C',
    'description': 'Temperatura objetivo para mantener cadena de frío',
    'default_value': 4.0
},

{
    'name': 'Tiempo Entrega Objetivo',
    'initials': 'TEO',
    'type': 1,
    'unit': 'HORAS',
    'description': 'Tiempo objetivo promedio de entrega por cliente',
    'default_value': 0.3
},

{
    'name': 'Tiempo Entrega Proveedor 1',
    'initials': 'TE1',
    'type': 1,
    'unit': 'DIAS',
    'description': 'Tiempo de entrega del proveedor principal',
    'default_value': 2
},

{
    'name': 'Tiempo Entrega Proveedor 2',
    'initials': 'TE2',
    'type': 1,
    'unit': 'DIAS',
    'description': 'Tiempo de entrega del proveedor secundario',
    'default_value': 3
},

{
    'name': 'Tiempo Entrega Proveedor 3',
    'initials': 'TE3',
    'type': 1,
    'unit': 'DIAS',
    'description': 'Tiempo de entrega del proveedor terciario',
    'default_value': 4
},

{
    'name': 'Peso Proveedor 1',
    'initials': 'P1',
    'type': 1,
    'unit': '%',
    'description': 'Participación porcentual del proveedor 1',
    'default_value': 0.5
},

{
    'name': 'Peso Proveedor 2',
    'initials': 'P2',
    'type': 1,
    'unit': '%',
    'description': 'Participación porcentual del proveedor 2',
    'default_value': 0.3
},

{
    'name': 'Peso Proveedor 3',
    'initials': 'P3',
    'type': 1,
    'unit': '%',
    'description': 'Participación porcentual del proveedor 3',
    'default_value': 0.2
},

{
    'name': 'Participación Mercado Competidor',
    'initials': 'PMC',
    'type': 1,
    'unit': '%',
    'description': 'Market share del principal competidor',
    'default_value': 30
},

{
    'name': 'Número Productos Competencia',
    'initials': 'NPC',
    'type': 1,
    'unit': 'PRODUCTOS',
    'description': 'Número de productos competidores en mercado',
    'default_value': 12
},

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

{
    'name': 'TOTAL CLIENTES ATENDIDOS',
    'initials': 'TCA',
    'type': 2,  # Estado
    'unit': 'CLIENTES',
    'description': 'TOTAL DE CLIENTES EN EL PERÍODO',
    'default_value': 0  # AGREGAR
},

{
    'name': 'Tiempo de Parada',
    'initials': 'TP',
    'type': 2,
    'unit': 'HORAS',
    'description': 'Horas de parada por mantenimiento y fallas',
    'default_value': 2
},

{
    'name': 'Cantidad Conforme',
    'initials': 'QC',
    'type': 2,
    'unit': 'L',
    'description': 'Productos que cumplen especificaciones de calidad',
    'default_value': 2450
},

{
    'name': 'Costo Reparaciones',
    'initials': 'CRP',
    'type': 2,
    'unit': 'BS',
    'description': 'Costo de reparaciones del día',
    'default_value': 500
},

{
    'name': 'Costo Repuestos',
    'initials': 'CREP',
    'type': 2,
    'unit': 'BS',
    'description': 'Costo de repuestos utilizados en el día',
    'default_value': 300
},

{
    'name': 'Costo Mano Obra Mantenimiento',
    'initials': 'CMOM',
    'type': 2,
    'unit': 'BS',
    'description': 'Costo de mano de obra de mantenimiento',
    'default_value': 400
},

{
    'name': 'Número de Fallas',
    'initials': 'NF',
    'type': 2,
    'unit': 'UNIDADES',
    'description': 'Número de fallas en equipos durante el día',
    'default_value': 1
},

{
    'name': 'Horas Mantenimiento Preventivo',
    'initials': 'HMP',
    'type': 2,
    'unit': 'HORAS',
    'description': 'Horas dedicadas a mantenimiento preventivo',
    'default_value': 1.5
},

{
    'name': 'Horas Mantenimiento Correctivo',
    'initials': 'HMC',
    'type': 2,
    'unit': 'HORAS',
    'description': 'Horas dedicadas a mantenimiento correctivo',
    'default_value': 0.5
},

{
    'name': 'Costo de Compra',
    'initials': 'CC',
    'type': 2,
    'unit': 'BS',
    'description': 'Costo de compra de materias primas del día',
    'default_value': 18000
},

{
    'name': 'Costo de Transporte Insumos',
    'initials': 'CTI',
    'type': 2,
    'unit': 'BS',
    'description': 'Costo de transporte de insumos',
    'default_value': 500
},

{
    'name': 'Costo de Almacenamiento',
    'initials': 'CAL',
    'type': 2,
    'unit': 'BS',
    'description': 'Costo de almacenamiento de insumos',
    'default_value': 200
},

{
    'name': 'Calidad Materia Prima 1',
    'initials': 'CMP1',
    'type': 2,
    'unit': 'PUNTOS',
    'description': 'Calificación de calidad proveedor 1 (1-10)',
    'default_value': 8.5
},

{
    'name': 'Calidad Materia Prima 2',
    'initials': 'CMP2',
    'type': 2,
    'unit': 'PUNTOS',
    'description': 'Calificación de calidad proveedor 2 (1-10)',
    'default_value': 7.8
},

{
    'name': 'Calidad Materia Prima 3',
    'initials': 'CMP3',
    'type': 2,
    'unit': 'PUNTOS',
    'description': 'Calificación de calidad proveedor 3 (1-10)',
    'default_value': 8.2
},

{
    'name': 'Volumen Proveedor 1',
    'initials': 'V1',
    'type': 2,
    'unit': 'L',
    'description': 'Volumen suministrado por proveedor 1',
    'default_value': 1250
},

{
    'name': 'Volumen Proveedor 2',
    'initials': 'V2',
    'type': 2,
    'unit': 'L',
    'description': 'Volumen suministrado por proveedor 2',
    'default_value': 750
},

{
    'name': 'Volumen Proveedor 3',
    'initials': 'V3',
    'type': 2,
    'unit': 'L',
    'description': 'Volumen suministrado por proveedor 3',
    'default_value': 500
},

{
    'name': 'Inventario Final Insumos',
    'initials': 'IIF',
    'type': 2,
    'unit': 'L',
    'description': 'Inventario final de insumos del día',
    'default_value': 8000
},

{
    'name': 'Entregas a Tiempo',
    'initials': 'EAT',
    'type': 2,
    'unit': 'UNIDADES',
    'description': 'Número de entregas realizadas a tiempo',
    'default_value': 28
},

{
    'name': 'Total de Entregas Proveedores',
    'initials': 'TTEP',
    'type': 2,
    'unit': 'UNIDADES',
    'description': 'Total de entregas programadas de proveedores',
    'default_value': 30
},

{
    'name': 'Empleados Salieron',
    'initials': 'ES',
    'type': 2,
    'unit': 'EMPLEADOS',
    'description': 'Empleados que salieron en el período',
    'default_value': 1
},

{
    'name': 'Empleados Entraron',
    'initials': 'EE',  # CORREGIDO: Cambiado de ED a EE para evitar duplicado
    'type': 2,
    'unit': 'EMPLEADOS',
    'description': 'Empleados que entraron en el período',
    'default_value': 1
},

{
    'name': 'Costo Capacitación Mensual',
    'initials': 'CCAP',
    'type': 2,
    'unit': 'BS/MES',
    'description': 'Costo mensual de capacitación de empleados',
    'default_value': 2000
},

{
    'name': 'Horas Ausentismo',
    'initials': 'HAU',
    'type': 2,
    'unit': 'HORAS',
    'description': 'Horas de ausentismo laboral del día',
    'default_value': 10
},

{
    'name': 'Horas Trabajadas Programadas',
    'initials': 'HTP',
    'type': 2,
    'unit': 'HORAS',
    'description': 'Horas programadas de trabajo del día',
    'default_value': 480
},

{
    'name': 'Leads Generados',
    'initials': 'LG',
    'type': 2,
    'unit': 'LEADS',
    'description': 'Número de leads generados por marketing',
    'default_value': 50
},

{
    'name': 'Nuevos Clientes',
    'initials': 'NC',
    'type': 2,
    'unit': 'CLIENTES',
    'description': 'Número de nuevos clientes adquiridos',
    'default_value': 15
},

{
    'name': 'Alcance de Campañas',
    'initials': 'AC',
    'type': 2,
    'unit': 'PERSONAS',
    'description': 'Alcance de las campañas publicitarias',
    'default_value': 10000
},

{
    'name': 'Alcance Campañas',
    'initials': 'ALC',  # AGREGADA: Variable faltante
    'type': 2,
    'unit': 'PERSONAS',
    'description': 'Alcance real de las campañas publicitarias',
    'default_value': 10000
},

{
    'name': 'Marca Reconocimiento Espontáneo',
    'initials': 'MRE',
    'type': 2,
    'unit': '%',
    'description': 'Reconocimiento espontáneo de marca',
    'default_value': 25
},

{
    'name': 'Marca Reconocimiento Asistido',
    'initials': 'MRA',
    'type': 2,
    'unit': '%',
    'description': 'Reconocimiento asistido de marca',
    'default_value': 45
},

{
    'name': 'Calidad Diferenciada Producto',
    'initials': 'CDP',
    'type': 2,
    'unit': 'PUNTOS',
    'description': 'Calificación diferenciación por calidad (1-10)',
    'default_value': 7.5
},

{
    'name': 'Costo Competitivo Producto',
    'initials': 'CCP',
    'type': 2,
    'unit': 'PUNTOS',
    'description': 'Competitividad en costos (1-10)',
    'default_value': 8.0
},

{
    'name': 'Servicio Competitivo Producto',
    'initials': 'CSP',
    'type': 2,
    'unit': 'PUNTOS',
    'description': 'Competitividad en servicio (1-10)',
    'default_value': 8.5
},

{
    'name': 'Intensidad Campañas Competencia',
    'initials': 'ICC',
    'type': 2,
    'unit': 'INDICE',
    'description': 'Intensidad de campañas de competencia (1-10)',
    'default_value': 6
},

{
    'name': 'Kilómetros Totales',
    'initials': 'KMT',
    'type': 2,
    'unit': 'KM',
    'description': 'Kilómetros totales recorridos en distribución',
    'default_value': 250
},

{
    'name': 'Costo Cadena Frío',
    'initials': 'CCF',
    'type': 2,
    'unit': 'BS',
    'description': 'Costo de mantener cadena de frío',
    'default_value': 300
},

{
    'name': 'Costo Logístico',
    'initials': 'CLOG',
    'type': 2,
    'unit': 'BS',
    'description': 'Otros costos logísticos del día',
    'default_value': 200
},

{
    'name': 'Tiempo Total Entregas Distribución',
    'initials': 'TTED',  # AGREGADA: Variable faltante
    'type': 2,
    'unit': 'HORAS',
    'description': 'Tiempo total empleado en entregas de distribución',
    'default_value': 8
},

{
    'name': 'Número de Entregas',
    'initials': 'NE',
    'type': 2,
    'unit': 'ENTREGAS',
    'description': 'Número total de entregas realizadas',
    'default_value': 25
},

{
    'name': 'Temperatura Cadena Frío',
    'initials': 'TCF',
    'type': 2,
    'unit': '°C',
    'description': 'Temperatura promedio mantenida en cadena frío',
    'default_value': 4.2
},

{
    'name': 'Tiempo Entrega Real',
    'initials': 'TER',
    'type': 2,
    'unit': 'HORAS',
    'description': 'Tiempo real promedio de entrega por cliente',
    'default_value': 0.32
},

{
    'name': 'Productos Devueltos',
    'initials': 'PD',
    'type': 2,
    'unit': 'L',
    'description': 'Litros de productos devueltos por problemas',
    'default_value': 25
},

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
    "name": "Merma Producción Calculada",
    "initials": "MP",  # AGREGADA: Variable faltante
    "type": 3,
    "unit": "L",
    "description": "Pérdida en el proceso de producción",
    "default_value": 0  # Calculada
},
  {
    "name": "Merma Inventario Calculada",
    "initials": "MI",  # AGREGADA: Variable faltante
    "type": 3,
    "unit": "L",
    "description": "Pérdida en inventario por deterioro o vencimiento",
    "default_value": 0  # Calculada
},
  {
    "name": "Costo Total Mermas Calculado",
    "initials": "CTM",  # AGREGADA: Variable faltante
    "type": 3,
    "unit": "Bs",
    "description": "Costo monetario total de las mermas en producción e inventario",
    "default_value": 0  # Calculada
},
  {
    "name": "Eficiencia Operativa Global Calculada",
    "initials": "EOG",  # AGREGADA: Variable faltante
    "type": 3,
    "unit": "%",
    "description": "Índice de eficiencia general de las operaciones",
    "default_value": 0  # Calculada
},
  {
    "name": "Índice Satisfacción Cliente Calculado",
    "initials": "ISC",  # AGREGADA: Variable faltante
    "type": 3,
    "unit": "%",
    "description": "Medición del nivel de satisfacción de los clientes",
    "default_value": 0  # Calculada
},
  {
    'name': 'Punto de Equilibrio Diario',
    'initials': 'PED',
    'type': 3,
    'unit': 'L',
    'description': 'Punto de equilibrio financiero calculado diariamente',
    'default_value': 1800  # CAMBIAR de 2000 a 1800
},

# ================================================================
# VARIABLES CALCULADAS ADICIONALES (TIPO 3) - KPIS POR ÁREA
# ================================================================

# MANTENIMIENTO - KPIs
{
    'name': 'Disponibilidad',
    'initials': 'DISP',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje de disponibilidad de equipos',
    'default_value': 0
},

{
    'name': 'Efectividad General Equipos',
    'initials': 'OEE',
    'type': 3,
    'unit': '%',
    'description': 'Overall Equipment Effectiveness',
    'default_value': 0
},

{
    'name': 'Costo Mantenimiento por Litro',
    'initials': 'CML',
    'type': 3,
    'unit': 'BS/L',
    'description': 'Costo unitario de mantenimiento',
    'default_value': 0
},

{
    'name': 'Frecuencia de Fallas',
    'initials': 'FF',
    'type': 3,
    'unit': 'FALLAS/1000H',
    'description': 'Fallas por cada 1000 horas de operación',
    'default_value': 0
},

{
    'name': 'Ratio Mantenimiento Preventivo',
    'initials': 'RMP',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje de mantenimiento preventivo',
    'default_value': 0
},

# ABASTECIMIENTO - KPIs
{
    'name': 'Costo Total de Adquisición',
    'initials': 'CTA',
    'type': 3,
    'unit': 'BS',
    'description': 'Costo total de adquisición de insumos',
    'default_value': 0
},

{
    'name': 'Tiempo Promedio Entrega Proveedores',
    'initials': 'TPEP',  # AGREGADA: Variable faltante
    'type': 3,
    'unit': 'DIAS',
    'description': 'Tiempo promedio ponderado de entrega de proveedores',
    'default_value': 0
},

{
    'name': 'Índice Calidad Proveedores',
    'initials': 'ICP',
    'type': 3,
    'unit': 'PUNTOS',
    'description': 'Calidad promedio ponderada de proveedores',
    'default_value': 0
},

{
    'name': 'Rotación Inventario Materias Primas',
    'initials': 'RIMP',
    'type': 3,
    'unit': 'VECES/AÑO',
    'description': 'Rotación anual de inventario de materias primas',
    'default_value': 0
},

{
    'name': 'Cumplimiento Entregas',
    'initials': 'CDE',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje de entregas a tiempo',
    'default_value': 0
},

# RECURSOS HUMANOS - KPIs
{
    'name': 'Índice Rotación Personal',
    'initials': 'IRP',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje anual de rotación de personal',
    'default_value': 0
},

{
    'name': 'Productividad por Empleado',
    'initials': 'PPE',
    'type': 3,
    'unit': 'L/EMPLEADO',
    'description': 'Productividad diaria por empleado',
    'default_value': 0
},

{
    'name': 'Costo Capacitación por Empleado',
    'initials': 'CCE',
    'type': 3,
    'unit': 'BS/EMPLEADO',
    'description': 'Inversión anual en capacitación por empleado',
    'default_value': 0
},

{
    'name': 'Tasa Ausentismo',
    'initials': 'TAU',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje de ausentismo laboral',
    'default_value': 0
},

{
    'name': 'Costo Laboral por Litro',
    'initials': 'CLL',
    'type': 3,
    'unit': 'BS/L',
    'description': 'Costo de mano de obra por litro producido',
    'default_value': 0
},

# MARKETING - KPIs
{
    'name': 'ROI Inversión Publicitaria',
    'initials': 'ROIA',
    'type': 3,
    'unit': '%',
    'description': 'Retorno de inversión publicitaria',
    'default_value': 0
},

{
    'name': 'Costo por Lead',
    'initials': 'CPL_MKT',  # Renombrado para evitar conflicto con CPL
    'type': 3,
    'unit': 'BS/LEAD',
    'description': 'Costo por lead generado',
    'default_value': 0
},

{
    'name': 'Tasa Conversión Leads',
    'initials': 'TCL',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje de conversión de leads a clientes',
    'default_value': 0
},

{
    'name': 'Alcance Efectivo Campañas',
    'initials': 'AEC',
    'type': 3,
    'unit': 'PERSONAS',
    'description': 'Alcance efectivo ponderado por conversión',
    'default_value': 0
},

{
    'name': 'Reconocimiento Marca Índice',
    'initials': 'RMI',
    'type': 3,
    'unit': 'PUNTOS',
    'description': 'Índice global de reconocimiento de marca',
    'default_value': 0
},

# COMPETENCIA - KPIs
{
    'name': 'Ventaja Competitiva Precio',
    'initials': 'VCP',
    'type': 3,
    'unit': '%',
    'description': 'Ventaja o desventaja en precio vs competencia',
    'default_value': 0
},

{
    'name': 'Participación Mercado Relativa',
    'initials': 'PMR',
    'type': 3,
    'unit': 'RATIO',
    'description': 'Market share relativo vs principal competidor',
    'default_value': 0
},

{
    'name': 'Índice Diferenciación Producto',
    'initials': 'IDP',
    'type': 3,
    'unit': 'PUNTOS',
    'description': 'Nivel de diferenciación del producto',
    'default_value': 0
},

{
    'name': 'Efectividad Estrategia Competitiva',
    'initials': 'EEC',
    'type': 3,
    'unit': 'PUNTOS',
    'description': 'Efectividad estratégica global vs competencia',
    'default_value': 0
},

{
    'name': 'Amenaza Competitiva',
    'initials': 'AMEN',  # AGREGADA: Variable faltante
    'type': 3,
    'unit': 'INDICE',
    'description': 'Nivel de amenaza competitiva en el mercado',
    'default_value': 0
},

# DISTRIBUCIÓN - KPIs
{
    'name': 'Eficiencia Rutas Entrega',
    'initials': 'ERE',
    'type': 3,
    'unit': 'L/KM',
    'description': 'Litros entregados por kilómetro recorrido',
    'default_value': 0
},

{
    'name': 'Costo Distribución por Litro',
    'initials': 'CDL',
    'type': 3,
    'unit': 'BS/L',
    'description': 'Costo unitario de distribución',
    'default_value': 0
},

{
    'name': 'Tiempo Promedio Entrega Cliente',
    'initials': 'TPEC',
    'type': 3,
    'unit': 'HORAS',
    'description': 'Tiempo promedio de entrega por cliente',
    'default_value': 0
},

{
    'name': 'Índice Calidad Entrega',
    'initials': 'ICE',
    'type': 3,
    'unit': 'INDICE',
    'description': 'Calidad del proceso de entrega',
    'default_value': 0
},

{
    'name': 'Tasa Devoluciones',
    'initials': 'TD',
    'type': 3,
    'unit': '%',
    'description': 'Porcentaje de productos devueltos',
    'default_value': 0
}

]
