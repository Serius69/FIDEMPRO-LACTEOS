questionary_data = [
    {'questionary': 'Cuestionario para registro de informacion de: ',
    },
        ]
question_data = [
    {
        'question': '¿Cuántos productos lácteos vende diariamente?',
        'type': 1,
        'initials_variable': 'CPVD',
    },
    {
        'question': '¿Cuál es el precio actual del producto?',
        'type': 1,
        'initials_variable': 'PVP',
    },
    {
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'type': 3,
        'initials_variable': 'DH',
    },
    {
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'type': 1,
        'initials_variable': 'CPROD',
    },
    {
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'type': 1,
        'initials_variable': 'DE',
    },
    {
        'question': '¿Cuál es el costo unitario de producción?',
        'type': 1,
        'initials_variable': 'CPU',
    },
    {
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'type': 1,
        'initials_variable': 'CIP',
    },
    {
        'question': '¿Existe estacionalidad en la demanda?',
        'type': 2,
        'initials_variable': 'ED',
        'possible_answers': ['Si', 'No'] 
    },
    {
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'type': 1,
        'initials_variable': 'CUIP',
    },
    {
        'question': '¿Cuál es el nivel de competitividad en el mercado de su empresa?',
        'type': 2,
        'initials_variable': 'NCM',
        'possible_answers': ['Muy competitivo', 'Medianamente competitivo', 'Poco competitivo'] 
    },
    {
        'question': '¿Cómo se posiciona su empresa en el mercado?',
        'type': 2,
        'initials_variable': 'PE',
        'possible_answers': ['No responde', 'Seguidor', 'Lider']
    },
    {
        'question': '¿Con qué frecuencia compran los clientes?',
        'type': 2,
        'initials_variable': 'FC',
        'possible_answers': ['Diaria','Semanal','Quincenal','Mensual']
    },
    {
        'question': '¿Cuál es la tasa de retención de clientes de su empresa?',
        'type': 1,
        'initials_variable': 'TRC',
    },
    {
        'question': '¿Cuál es el nivel de satisfacción del cliente?',
        'type': 1,
        'initials_variable': 'SC',
    },
    {
        'question': '¿Cuál es el nivel de lealtad del cliente?',
        'type': 1,
        'initials_variable': 'NLC',
        'possible_answers': ['Muy competitivo', 'Medianamente competitivo', 'Poco competitivo'] 
    },
    {
        'question': '¿Cuánto cuesta adquirir un nuevo cliente?',
        'type': 1,
        'initials_variable': 'CUAC',
    },
    {
        'question': '¿Cuánto cuesta retener a un cliente?',
        'type': 1,
        'initials_variable': 'CURC',
    },
    {
        'question': '¿Cuántos clientes llegan diariamente?',
        'type': 1,
        'initials_variable': 'CPD',
    },
    {
        'question': '¿Cuál es el nivel de automatización del proceso de producción?',
        'type': 2,
        'initials_variable': 'NAPP',
        'possible_answers': ['Totalmente automatizado','Parcialmente automatizado','Manual']
    },
    {
        'question': '¿Cuál es el nivel de eficiencia del proceso de producción?',
        'type': 2,
        'initials_variable': 'NEPP',
        'possible_answers': ['Alto','Medio','Bajo']
    },
    {
        'question': '¿La empresa cuenta con certificaciones de calidad?',
        'type': 2,
        'initials_variable': 'CERCAL',
        'possible_answers': ['ISO 9001', 'HACCP', 'Ninguna']
    },
    {
        'question': '¿Cuánto tiempo tarda en producir un producto?',
        'type': 1,
        'initials_variable': 'TPP',
    },
    {
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'type': 1,
        'initials_variable': 'CPROD',
    },
    {
        'question': '¿Cuál es el nivel de flexibilidad en la producción?',
        'type': 2,
        'initials_variable': 'NFP',
        'possible_answers': ['Alto','Medio','Bajo']
    },
    {
        'question': '¿Cuál es el nivel de eficiencia del inventario?',
        'type': 2,
        'initials_variable': 'NEI',
        'possible_answers': ['Alto','Medio','Bajo']
    },
    {
        'question': '¿Cuál es el nivel de eficiencia en la cadena de suministro?',
        'type': 2,
        'initials_variable': 'NECS',
        'possible_answers': ['Alto','Medio','Bajo']
    },
    {
        'question': '¿Cuál es el nivel de eficiencia en la gestión de compra de insumos?',
        'type': 2,
        'initials_variable': 'NEGCI',
        'possible_answers': ['Alto','Medio','Bajo']
    },
    {
        'question': '¿Cuál es el nivel de eficiencia en la gestión de ventas?',
        'type': 1,
        'initials_variable': 'NEGV',
        'possible_answers': ['Alto','Medio','Bajo']
    },
    {
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'type': 1,
        'initials_variable': 'SE',
    },
    {
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'type': 1,
        'initials_variable': 'PVPCC',
    },
    {
        'question': '¿Cuál es el costo fijo diario?',
        'type': 1,
        'initials_variable': 'CFD',
    },
    {
        'question': '¿Cuál es el costo unitario por transporte?',
        'type': 1,
        'initials_variable': 'CUTRANS',
    },
    {
        'question': '¿Cuál es el costo unitario del inventario?',
        'type': 1,
        'initials_variable': 'CUI',
    },
    {
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'type': 1,
        'initials_variable': 'GMM',
    },
    {
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'type': 1,
        'initials_variable': 'TR',
    },
    {
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'type': 1,
        'initials_variable': 'CIP',
    },
    {
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'type': 1,
        'initials_variable': 'CMIPF',
    },
    {
        'question': '¿Cuántos artículos produce en cada lote de producción?',
        'type': 1,
        'initials_variable': 'ALEP'
    },
    {
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?', 
        'type': 1,
        'initials_variable': 'TE'  
    },
]