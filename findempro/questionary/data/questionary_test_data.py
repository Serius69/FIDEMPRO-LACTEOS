questionary_data = [
    {
        'questionary': 'Cuestionario completo para registro de información empresarial',
        'description': 'Este cuestionario recopila toda la información necesaria para simular la operación de su empresa láctea',
    }
]

question_data = [
    # SECCIÓN 1: DEMANDA Y VENTAS
    {
        'section': 'Demanda y Ventas',
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'type': 3,  # Lista de valores
        'initials_variable': 'DH',
        'unit': 'Litros/día',
        'help_text': 'Ingrese los valores de venta diaria del último mes separados por comas',
        # 'validation': 'min_length:30',
        # 'required': True
    },
    {
        'section': 'Demanda y Ventas',
        'question': '¿Cuál es el precio actual de venta del producto?',
        'type': 1,  # Respuesta numérica
        'initials_variable': 'PVP',
        'unit': 'Bs/L',
        'help_text': 'Precio de venta al público de su producto principal',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Demanda y Ventas',
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'type': 1,
        'initials_variable': 'DE',
        'unit': 'Litros/día',
        'help_text': 'Estimación de demanda futura basada en tendencias o pedidos',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Demanda y Ventas',
        'question': '¿Existe estacionalidad en la demanda?',
        'type': 2,  # Opción múltiple
        'initials_variable': 'ED',
        'possible_answers': ['Sí', 'No'],
        'help_text': 'Indique si las ventas varían según temporadas (escolar, fiestas, etc.)',
        # 'conversion': {'Sí': 1.2, 'No': 1.0},  # Factor de estacionalidad
        # 'required': True
    },
    {
        'section': 'Demanda y Ventas',
        'question': '¿Cuántos clientes llegan diariamente?',
        'type': 1,
        'initials_variable': 'CPD',
        'unit': 'clientes/día',
        'help_text': 'Número promedio de clientes únicos atendidos por día',
        # 'validation': 'min:1',
        # 'required': True
    },
    {
        'section': 'Demanda y Ventas',
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'type': 1,
        'initials_variable': 'TPC',
        'unit': 'días',
        'help_text': 'Cada cuántos días regresan sus clientes frecuentes',
        # 'validation': 'min:1,max:30',
        # 'required': True
    },
    {
        'section': 'Demanda y Ventas',
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'type': 1,
        'initials_variable': 'PC',
        'unit': 'Bs/L',
        'help_text': 'Precio de venta de productos lácteos similares en el mercado',
        # 'validation': 'min:0',
        # 'required': True
    },

    # SECCIÓN 2: PRODUCCIÓN
    {
        'section': 'Producción',
        'question': '¿Cuál es la cantidad producida diariamente?',
        'type': 1,
        'initials_variable': 'QPL',
        'unit': 'Litros/día',
        'help_text': 'Producción diaria promedio actual de su planta',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Producción',
        'question': '¿Cuál es la capacidad de producción diaria?',
        'type': 1,
        'initials_variable': 'CPROD',
        'unit': 'Litros/día',
        'help_text': 'Máxima cantidad que puede producir en un día con todos los recursos',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Producción',
        'question': '¿Cuál es el número de empleados?',
        'type': 1,
        'initials_variable': 'NEPP',
        'unit': 'empleados',
        'help_text': 'Total de empleados directamente involucrados en producción',
        # 'validation': 'min:1',
        # 'required': True
    },
    {
        'section': 'Producción',
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'type': 1,
        'initials_variable': 'TPE',
        'unit': 'minutos/100L',
        'help_text': 'Tiempo promedio de trabajo por cada 100 litros producidos',
        # 'validation': 'min:1',
        # 'required': True
    },
    {
        'section': 'Producción',
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'type': 1,
        'initials_variable': 'CPPL',
        'unit': 'Litros/lote',
        'help_text': 'Cantidad típica producida en cada lote o tanda',
        # 'validation': 'min:1',
        # 'required': True
    },
    # {
    #     'section': 'Producción',
    #     'question': '¿Cuántos minutos laborables tiene por día?',
    #     'type': 1,
    #     'initials_variable': 'MLP',
    #     'unit': 'minutos',
    #     'help_text': 'Total de minutos de trabajo efectivo por día (ej: 480 para 8 horas)',
    #     'validation': 'min:60,max:1440',
    #     # 'default_value': 480,
    #     # 'required': True
    # },

    # SECCIÓN 3: INVENTARIOS
    {
        'section': 'Inventarios',
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'type': 1,
        'initials_variable': 'CMIPF',
        'unit': 'Litros',
        'help_text': 'Capacidad total de sus cámaras frigoríficas o almacén',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Inventarios',
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'type': 1,
        'initials_variable': 'CIP',
        'unit': 'Litros',
        'help_text': 'Capacidad utilizable actual de almacenamiento',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Inventarios',
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'type': 1,
        'initials_variable': 'SI',
        'unit': 'Litros',
        'help_text': 'Inventario mínimo para evitar desabastecimiento',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Inventarios',
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'type': 1,
        'initials_variable': 'TR',
        'unit': 'días',
        'help_text': 'Frecuencia de compra de materia prima',
        # 'validation': 'min:1,max:7',
        # 'required': True
    },
    {
        'section': 'Inventarios',
        'question': '¿Días promedio de reabastecimiento?',
        'type': 1,
        'initials_variable': 'DPL',
        'unit': 'días',
        'help_text': 'Lead time desde que pide hasta que recibe la materia prima',
        # 'validation': 'min:0,max:7',
        # 'required': True
    },
    {
        'section': 'Inventarios',
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'type': 1,
        'initials_variable': 'TMP',
        'unit': 'días',
        'help_text': 'Tiempo desde que recibe un pedido hasta que lo entrega',
        # 'validation': 'min:0,max:3',
        # 'required': True
    },

    # SECCIÓN 4: COSTOS Y FINANZAS
    {
        'section': 'Costos y Finanzas',
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'type': 1,
        'initials_variable': 'CUIP',
        'unit': 'Bs/L',
        'help_text': 'Costo por litro de leche cruda o insumo principal',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Costos y Finanzas',
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'type': 1,
        'initials_variable': 'CINSP',
        'unit': 'L insumo/L producto',
        'help_text': 'Factor de conversión de materia prima a producto terminado',
        # 'validation': 'min:0.5,max:15',
        # 'required': True
    },
    {
        'section': 'Costos y Finanzas',
        'question': '¿Cuál es el costo fijo diario?',
        'type': 1,
        'initials_variable': 'CFD',
        'unit': 'Bs/día',
        'help_text': 'Incluye alquiler, servicios básicos, seguros, etc.',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Costos y Finanzas',
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'type': 1,
        'initials_variable': 'SE',
        'unit': 'Bs/mes',
        'help_text': 'Suma total de la planilla mensual de todos los empleados',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Costos y Finanzas',
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'type': 1,
        'initials_variable': 'GMM',
        'unit': 'Bs/mes',
        'help_text': 'Gastos en publicidad, promociones, redes sociales, etc.',
        # 'validation': 'min:0',
        # 'required': True
    },

    # SECCIÓN 5: LOGÍSTICA Y DISTRIBUCIÓN
    {
        'section': 'Logística',
        'question': '¿Cuál es el costo unitario por transporte?',
        'type': 1,
        'initials_variable': 'CUTRANS',
        'unit': 'Bs/L',
        'help_text': 'Costo de transportar un litro de producto hasta el cliente',
        # 'validation': 'min:0',
        # 'required': True
    },
    {
        'section': 'Logística',
        'question': '¿Cuántos litros se transportan por viaje?',
        'type': 1,
        'initials_variable': 'CTPLV',
        'unit': 'Litros/viaje',
        'help_text': 'Capacidad de su vehículo o medio de transporte',
        # 'validation': 'min:1',
        # 'required': True
    }

]

# # Validaciones adicionales para el cuestionario
# question_validations = {
#     'cross_validations': [
#         {
#             'rule': 'QPL <= CPROD',
#             'message': 'La producción diaria no puede ser mayor que la capacidad máxima'
#         },
#         {
#             'rule': 'CIP <= CMIPF',
#             'message': 'La capacidad actual no puede ser mayor que la capacidad máxima'
#         },
#         {
#             'rule': 'mean(DH) * 0.5 <= QPL <= mean(DH) * 1.5',
#             'message': 'La producción debe estar entre 50% y 150% de la demanda promedio histórica'
#         },
#         {
#             'rule': 'CUIP < PVP * 0.7',
#             'message': 'El costo de materia prima debe ser menor al 70% del precio de venta'
#         },
#         {
#             'rule': 'TPE * NEPP <= MLP',
#             'message': 'El tiempo total de producción no puede exceder las horas laborables'
#         }
#     ]
# }

# # Agrupación de preguntas por criticidad
# question_priority = {
#     'critical': [  # Preguntas esenciales para el modelo
#         'DH', 'PVP', 'CUIP', 'QPL', 'CPROD', 'NEPP', 'SE', 'CFD'
#     ],
#     'important': [  # Preguntas importantes pero con defaults razonables
#         'DE', 'CPD', 'CINSP', 'TR', 'CMIPF', 'GMM', 'CUTRANS'
#     ],
#     'optional': [  # Preguntas que pueden usar valores calculados
#         'IPF', 'II', 'VPC', 'ED', 'SI', 'TPC'
#     ]
# }

# # Función para calcular valores por defecto inteligentes
# def calculate_intelligent_defaults(answers):
#     """
#     Calcula valores por defecto basados en las respuestas ya proporcionadas
#     """
#     defaults = {}
    
#     # Si tenemos demanda histórica, calcular promedios
#     if 'DH' in answers and isinstance(answers['DH'], list):
#         dph = sum(answers['DH']) / len(answers['DH'])
        
#         # Inventario inicial sugerido: 2 días de demanda
#         if 'IPF' not in answers:
#             defaults['IPF'] = dph * 2
            
#         # Inventario de insumos: 3 días de producción
#         if 'II' not in answers and 'CINSP' in answers:
#             defaults['II'] = dph * answers['CINSP'] * 3
            
#         # Ventas por cliente
#         if 'VPC' not in answers and 'CPD' in answers:
#             defaults['VPC'] = dph / answers['CPD']
            
#         # Demanda esperada: promedio histórico + 5%
#         if 'DE' not in answers:
#             defaults['DE'] = dph * 1.05
            
#         # Stock de seguridad: 1 día de demanda
#         if 'SI' not in answers:
#             defaults['SI'] = dph
    
#     return defaults

# # Función para generar resumen del cuestionario
# def generate_questionnaire_summary(answers):
#     """
#     Genera un resumen de las respuestas para validación
#     """
#     if 'DH' in answers and isinstance(answers['DH'], list):
#         dph = sum(answers['DH']) / len(answers['DH'])
#         dsd = (sum((x - dph) ** 2 for x in answers['DH']) / len(answers['DH'])) ** 0.5
        
#         summary = {
#             'demanda_promedio_historica': round(dph, 2),
#             'desviacion_estandar': round(dsd, 2),
#             'coeficiente_variacion': round(dsd / dph, 3),
#             'capacidad_utilizada': round(answers.get('QPL', 0) / answers.get('CPROD', 1), 2),
#             'margen_bruto_esperado': round((answers.get('PVP', 0) - answers.get('CUIP', 0)) / answers.get('PVP', 1), 2),
#             'dias_inventario_objetivo': round(answers.get('SI', 0) / dph, 1) if dph > 0 else 0
#         }
        
#         return summary
    
#     return None