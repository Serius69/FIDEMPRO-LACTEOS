# questionary_data.py - Versión Corregida con mapeo correcto de variables
questionary_data = [
    {
        'questionary': 'Cuestionario para registro de información',
    },
]

question_data = [
    {
        'question': '¿Cuál es el precio actual del producto?',
        'type': 1,  # Respuesta numérica
        'initials_variable': 'PVP',
        'unit': 'Bs/L',
        'help_text': 'Ingrese el precio de venta actual de su producto principal'
    },
    {
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'type': 3,  # Lista de valores
        'initials_variable': 'DH',
        'unit': 'Litros/día',
        'help_text': 'Ingrese los valores separados por comas'
    },
    {
        'question': '¿Cuál es la cantidad producida diariamente?',
        'type': 1,
        'initials_variable': 'QPL',
        'unit': 'Litros/día',
        'help_text': 'Cantidad promedio de productos lácteos producidos por día'
    },
    {
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'type': 1,
        'initials_variable': 'DE',
        'unit': 'Litros/día',
        'help_text': 'Estimación de la demanda futura basada en tendencias'
    },
    {
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'type': 1,
        'initials_variable': 'CIP',
        'unit': 'Litros',
        'help_text': 'Capacidad máxima de almacenamiento de productos terminados'
    },
    {
        'question': '¿Existe estacionalidad en la demanda?',
        'type': 2,  # Opción múltiple
        'initials_variable': 'ED',
        'possible_answers': ['Sí', 'No'],
        'help_text': 'Indique si la demanda varía según la temporada'
    },
    {
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'type': 1,
        'initials_variable': 'CUIP',
        'unit': 'Bs/L',
        'help_text': 'Costo de la materia prima por litro'
    },
    {
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'type': 1,
        'initials_variable': 'TPC',
        'unit': 'días',
        'help_text': 'Cada cuántos días compran sus clientes habituales'
    },
    {
        'question': '¿Cuántos clientes llegan diariamente?',
        'type': 1,
        'initials_variable': 'CPD',
        'unit': 'clientes/día',
        'help_text': 'Número promedio de clientes atendidos por día'
    },
    {
        'question': '¿Cuál es el número de empleados?',
        'type': 1,
        'initials_variable': 'NEPP',
        'unit': 'empleados',
        'help_text': 'Total de empleados en producción'
    },
    {
        'question': '¿Cuál es la capacidad de producción diaria?',
        'type': 1,
        'initials_variable': 'CPROD',
        'unit': 'Litros/día',
        'help_text': 'Capacidad máxima de producción por día'
    },
    {
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'type': 1,
        'initials_variable': 'SE',
        'unit': 'Bs/mes',
        'help_text': 'Suma total de sueldos mensuales'
    },
    {
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'type': 1,
        'initials_variable': 'PC',
        'unit': 'Bs/L',
        'help_text': 'Precio de venta de productos similares en el mercado'
    },
    {
        'question': '¿Cuál es el costo fijo diario?',
        'type': 1,
        'initials_variable': 'CFD',
        'unit': 'Bs/día',
        'help_text': 'Costos fijos diarios (alquiler, servicios, etc.)'
    },
    {
        'question': '¿Cuál es el costo unitario por transporte?',
        'type': 1,
        'initials_variable': 'CUTRANS',
        'unit': 'Bs/L',
        'help_text': 'Costo de transporte por litro de producto'
    },
    {
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'type': 1,
        'initials_variable': 'GMM',
        'unit': 'Bs/mes',
        'help_text': 'Inversión mensual en publicidad y promoción'
    },
    {
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'type': 1,
        'initials_variable': 'TR',
        'unit': 'días',
        'help_text': 'Frecuencia de reabastecimiento de materias primas'
    },
    {
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'type': 1,
        'initials_variable': 'CINSP',
        'unit': 'L insumo/L producto',
        'help_text': 'Relación de conversión insumo a producto'
    },
    {
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'type': 1,
        'initials_variable': 'CMIPF',
        'unit': 'Litros',
        'help_text': 'Capacidad total de almacenamiento de productos terminados'
    },
    {
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?', 
        'type': 1,
        'initials_variable': 'TPE',
        'unit': 'minutos/100L',
        'help_text': 'Tiempo de producción por cada 100 litros'
    },
    {
        'question': '¿Cuánto es la cantidad promedio producida por lote?', 
        'type': 1,
        'initials_variable': 'CPPL',
        'unit': 'Litros/lote',
        'help_text': 'Tamaño promedio de cada lote de producción'
    },
    {
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?', 
        'type': 1,
        'initials_variable': 'SI',
        'unit': 'Litros',
        'help_text': 'Inventario mínimo para evitar desabastecimiento'
    },
    {
        'question': '¿Días promedio de reabastecimiento?', 
        'type': 1,
        'initials_variable': 'DPL',
        'unit': 'días',
        'help_text': 'Tiempo que toma reabastecer el inventario'
    },
    {
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?', 
        'type': 1,
        'initials_variable': 'TMP',
        'unit': 'días',
        'help_text': 'Tiempo desde el pedido hasta la entrega'
    },
    {
        'question': '¿Cuántos litros se transportan por viaje?', 
        'type': 1,
        'initials_variable': 'CTPLV',
        'unit': 'Litros/viaje',
        'help_text': 'Capacidad de transporte por viaje'
    },
    {
        'question': '¿Cuántos proveedores de leche tiene?', 
        'type': 1,
        'initials_variable': 'NPD',
        'unit': 'proveedores',
        'help_text': 'Número total de proveedores activos'
    },
    {
        'question': '¿Cuál es el consumo diario promedio de leche?', 
        'type': 1,
        'initials_variable': 'CTL',
        'unit': 'Litros/día',
        'help_text': 'Consumo promedio diario de materia prima'
    },
    {
        'question': '¿Cuál es la cantidad promedio total producida por lote?', 
        'type': 1,
        'initials_variable': 'CPL',
        'unit': 'Litros',
        'help_text': 'Producción total promedio por lote'
    },
]

