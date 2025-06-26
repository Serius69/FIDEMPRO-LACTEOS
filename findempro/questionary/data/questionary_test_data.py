# questionary_test_data_complete.py - Cuestionario completo sincronizado con questionary_result_test_data

questionary_data = [
    {
        'questionary': 'Cuestionario completo para registro de información empresarial',
        'description': 'Este cuestionario recopila toda la información necesaria para simular la operación de su empresa láctea',
    }
]

question_data = [
    # 1. Precio de venta
    {
        'section': 'Precio y Ventas',
        'question': '¿Cuál es el precio actual del producto?',
        'type': 1,  # Respuesta numérica
        'initials_variable': 'PVP',
        'unit': 'Bs/L',
        'help_text': 'Precio basado en análisis de mercado local',
    },
    
    # 2. Datos históricos de demanda
    {
        'section': 'Demanda',
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'type': 3,  # Lista de valores
        'initials_variable': 'DH',
        'unit': 'Litros/día',
        'help_text': 'Datos reales de ventas del último mes',
    },
    
    # 3. Cantidad producida diariamente
    {
        'section': 'Producción',
        'question': '¿Cuál es la cantidad que produce diariamente en promedio?',
        'type': 1,
        'initials_variable': 'QPL',
        'unit': 'Litros/día',
        'help_text': 'Producción actual promedio diaria',
    },
    
    # 4. Demanda esperada
    {
        'section': 'Demanda',
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'type': 1,
        'initials_variable': 'DE',
        'unit': 'Litros/día',
        'help_text': 'Proyección basada en tendencias históricas',
    },
    
    # 5. Capacidad del inventario
    {
        'section': 'Inventarios',
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'type': 1,
        'initials_variable': 'CIP',
        'unit': 'Litros',
        'help_text': 'Capacidad de almacenamiento de productos terminados',
    },
    
    # 6. Estacionalidad de la demanda
    {
        'section': 'Demanda',
        'question': '¿Existe estacionalidad en la demanda?',
        'type': 2,  # Opción múltiple
        'initials_variable': 'ED',
        'possible_answers': ['Sí', 'No'],
        'help_text': 'Mayor demanda en época escolar y festividades',
    },
    
    # 7. Costo unitario del insumo
    {
        'section': 'Costos',
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'type': 1,
        'initials_variable': 'CUIP',
        'unit': 'Bs/L',
        'help_text': 'Costo de materia prima (leche cruda) por litro',
    },
    
    # 8. Tiempo promedio entre compras
    {
        'section': 'Ventas',
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'type': 1,
        'initials_variable': 'TPC',
        'unit': 'días',
        'help_text': 'Frecuencia de compra de clientes regulares',
    },
    
    # 9. Clientes por día
    {
        'section': 'Ventas',
        'question': '¿Cuántos clientes llegan diariamente?',
        'type': 1,
        'initials_variable': 'CPD',
        'unit': 'clientes/día',
        'help_text': 'Promedio de clientes atendidos por día',
    },
    
    # 10. Número de empleados
    {
        'section': 'Recursos Humanos',
        'question': '¿Cuál es el número de empleados?',
        'type': 1,
        'initials_variable': 'NEPP',
        'unit': 'empleados',
        'help_text': 'Personal total en producción',
    },
    
    # 11. Capacidad de producción diaria
    {
        'section': 'Producción',
        'question': '¿Cuál es la capacidad de producción diaria?',
        'type': 1,
        'initials_variable': 'CPROD',
        'unit': 'Litros/día',
        'help_text': 'Capacidad máxima de producción instalada',
    },
    
    # 12. Sueldos y salarios
    {
        'section': 'Recursos Humanos',
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'type': 1,
        'initials_variable': 'SE',
        'unit': 'Bs/mes',
        'help_text': 'Planilla total mensual de empleados',
    },
    
    # 13. Precio de la competencia
    {
        'section': 'Competencia',
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'type': 1,
        'initials_variable': 'PC',
        'unit': 'Bs/L',
        'help_text': 'Estudio de precios de la competencia directa',
    },
    
    # 14. Costo fijo diario
    {
        'section': 'Costos',
        'question': '¿Cuál es el costo fijo diario?',
        'type': 1,
        'initials_variable': 'CFD',
        'unit': 'Bs/día',
        'help_text': 'Costos fijos: alquiler, servicios básicos, seguros',
    },
    
    # 15. Costo unitario por transporte
    {
        'section': 'Logística',
        'question': '¿Cuál es el costo unitario por transporte?',
        'type': 1,
        'initials_variable': 'CUTRANS',
        'unit': 'Bs/L',
        'help_text': 'Costo de distribución por litro',
    },
    
    # 16. Gastos de marketing
    {
        'section': 'Marketing',
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'type': 1,
        'initials_variable': 'GMM',
        'unit': 'Bs/mes',
        'help_text': 'Inversión mensual en publicidad y promoción',
    },
    
    # 17. Tiempo de reabastecimiento
    {
        'section': 'Inventarios',
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'type': 1,
        'initials_variable': 'TR',
        'unit': 'días',
        'help_text': 'Frecuencia de compra de materia prima',
    },
    
    # 18. Conversión insumo-producto
    {
        'section': 'Producción',
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'type': 1,
        'initials_variable': 'CINSP',
        'unit': 'L insumo/L producto',
        'help_text': 'Factor de conversión insumo-producto',
    },
    
    # 19. Capacidad máxima de almacenamiento
    {
        'section': 'Inventarios',
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'type': 1,
        'initials_variable': 'CMIPF',
        'unit': 'Litros',
        'help_text': 'Capacidad total de almacén refrigerado',
    },
    
    # 20. Tiempo de producción por empleado
    {
        'section': 'Producción',
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'type': 1,
        'initials_variable': 'TPE',
        'unit': 'minutos/100L',
        'help_text': 'Tiempo de mano de obra por lote de 100L',
    },
    
    # 21. Cantidad promedio por lote
    {
        'section': 'Producción',
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'type': 1,
        'initials_variable': 'CPPL',
        'unit': 'Litros/lote',
        'help_text': 'Tamaño estándar de lote de producción',
    },
    
    # 22. Stock mínimo de seguridad
    {
        'section': 'Inventarios',
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'type': 1,
        'initials_variable': 'SI',
        'unit': 'Litros',
        'help_text': 'Inventario de seguridad para evitar roturas de stock',
    },
    
    # 23. Días promedio de reabastecimiento
    {
        'section': 'Inventarios',
        'question': '¿Días promedio de reabastecimiento?',
        'type': 1,
        'initials_variable': 'DPL',
        'unit': 'días',
        'help_text': 'Tiempo para reponer inventario desde pedido',
    },
    
    # 24. Tiempo medio de procesamiento
    {
        'section': 'Logística',
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'type': 1,
        'initials_variable': 'TMP',
        'unit': 'días',
        'help_text': 'Proceso ágil para pedidos pequeños',
    },
    
    # 25. Capacidad de transporte por viaje
    {
        'section': 'Logística',
        'question': '¿Cuántos litros se transportan por viaje?',
        'type': 1,
        'initials_variable': 'CTPLV',
        'unit': 'Litros/viaje',
        'help_text': 'Capacidad de transporte local',
    },
    
    # 26. Distancia promedio de entrega
    {
        'section': 'Logística',
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'type': 1,
        'initials_variable': 'DPE',
        'unit': 'KM',
        'help_text': 'Distancia media de distribución urbana',
    },
    
    # 27. Consumo diario promedio de materia prima
    {
        'section': 'Inventarios',
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'type': 1,
        'initials_variable': 'CTL',
        'unit': 'Litros/día',
        'help_text': 'Consumo de leche cruda para producción',
    },
    
    # 28. Minutos laborables por día
    {
        'section': 'Producción',
        'question': '¿Cuántos minutos laborables tiene por día?',
        'type': 1,
        'initials_variable': 'MLP',
        'unit': 'minutos',
        'help_text': 'Jornada laboral de 8 horas efectivas',
    },
    
    # 29. Días máximos de simulación
    {
        'section': 'Simulación',
        'question': '¿Cuántos días máximos planea simular?',
        'type': 1,
        'initials_variable': 'NMD',
        'unit': 'días',
        'help_text': 'Período de simulación de un mes',
    },
    
    # 30. Número de proveedores
    {
        'section': 'Proveedores',
        'question': '¿Cuántos proveedores de leche tiene?',
        'type': 1,
        'initials_variable': 'NPD',
        'unit': 'proveedores',
        'help_text': 'Red diversificada de proveedores locales',
    },
    
    # 31. Horas totales de operación
    {
        'section': 'Producción',
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'type': 1,
        'initials_variable': 'HTO',
        'unit': 'horas',
        'help_text': 'Operación continua con turnos',
    },
    
    # 32. Cantidad máxima producible
    {
        'section': 'Producción',
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'type': 1,
        'initials_variable': 'QMAX',
        'unit': 'Litros',
        'help_text': 'Capacidad teórica máxima al 100%',
    },
    
    # 33. Temperatura cadena de frío
    {
        'section': 'Control de Calidad',
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'type': 1,
        'initials_variable': 'TCFO',
        'unit': '°C',
        'help_text': 'Temperatura óptima para conservación láctea',
    },
    
    # 34. Tiempo objetivo de entrega
    {
        'section': 'Logística',
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'type': 1,
        'initials_variable': 'TEO',
        'unit': 'horas',
        'help_text': 'Tiempo máximo aceptable de entrega',
    },
    
    # 35. Tiempo entrega proveedor 1
    {
        'section': 'Proveedores',
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'type': 1,
        'initials_variable': 'TE1',
        'unit': 'días',
        'help_text': 'Lead time del proveedor más confiable',
    },
    
    # 36. Tiempo entrega proveedor 2
    {
        'section': 'Proveedores',
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'type': 1,
        'initials_variable': 'TE2',
        'unit': 'días',
        'help_text': 'Lead time del segundo proveedor',
    },
    
    # 37. Tiempo entrega proveedor 3
    {
        'section': 'Proveedores',
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'type': 1,
        'initials_variable': 'TE3',
        'unit': 'días',
        'help_text': 'Lead time del tercer proveedor',
    },
    
    # 38. Peso proveedor 1
    {
        'section': 'Proveedores',
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'type': 1,
        'initials_variable': 'P1',
        'unit': '%',
        'help_text': '50% del suministro del proveedor principal',
    },
    
    # 39. Peso proveedor 2
    {
        'section': 'Proveedores',
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'type': 1,
        'initials_variable': 'P2',
        'unit': '%',
        'help_text': '30% del suministro del proveedor secundario',
    },
    
    # 40. Peso proveedor 3
    {
        'section': 'Proveedores',
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'type': 1,
        'initials_variable': 'P3',
        'unit': '%',
        'help_text': '20% del suministro del proveedor terciario',
    },
    
    # 41. Participación de mercado del competidor
    {
        'section': 'Competencia',
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'type': 1,
        'initials_variable': 'PMC',
        'unit': '%',
        'help_text': 'Competidor líder con participación significativa',
    },
    
    # 42. Número de productos competidores
    {
        'section': 'Competencia',
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'type': 1,
        'initials_variable': 'NPC',
        'unit': 'productos',
        'help_text': 'Mercado con competencia moderada',
    },
]