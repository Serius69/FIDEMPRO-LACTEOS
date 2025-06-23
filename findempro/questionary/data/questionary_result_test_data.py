# questionary_result_data.py - Versión Adaptada y Completa
import random
import numpy as np


questionary_result_data = [
    {
        'name': 'Respuestas para el producto Leche',
        'product': 'Leche',
        'business_type': 'Pequeña empresa láctea',
        'location': 'La Paz, Bolivia', 
        'employees': 15,
        'years_in_business': 8
    },
    {
        'name': 'Respuestas para el producto Queso',
        'product': 'Queso',
        'business_type': 'Mediana empresa procesadora',
        'location': 'Cochabamba, Bolivia',
        'employees': 25,
        'years_in_business': 12
    },
    {
        'name': 'Respuestas para el producto Yogur', 
        'product': 'Yogur',
        'business_type': 'Pequeña empresa artesanal',
        'location': 'Santa Cruz, Bolivia',
        'employees': 10,
        'years_in_business': 5
    },
    {
        'name': 'Respuestas para el producto Mantequilla',
        'product': 'Mantequilla',
        'business_type': 'Pequeña empresa familiar',
        'location': 'Oruro, Bolivia',
        'employees': 8,
        'years_in_business': 4
    },
    {
        'name': 'Respuestas para el producto Crema de Leche',
        'product': 'Crema de Leche',
        'business_type': 'Microempresa láctea',
        'location': 'Potosí, Bolivia',
        'employees': 6,
        'years_in_business': 3
    },
    {
        'name': 'Respuestas para el producto Leche Deslactosada',
        'product': 'Leche Deslactosada',
        'business_type': 'Mediana empresa especializada',
        'location': 'Tarija, Bolivia',
        'employees': 12,
        'years_in_business': 6
    },
    {
        'name': 'Respuestas para el producto Dulce de Leche',
        'product': 'Dulce de Leche',
        'business_type': 'Pequeña empresa tradicional',
        'location': 'Sucre, Bolivia',
        'employees': 8,
        'years_in_business': 7
    }
]

answer_data_leche = [
    {
        'answer': 15.50,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'initials_variable': 'PVP',
        'justification': 'Precio basado en análisis de mercado local',
        'variable_name': 'precio_actual'
    },    
    {
        'answer': [2450, 2380, 2520, 2490, 2600, 2350, 2400, 2550, 2480, 2520,
                  2580, 2620, 2490, 2510, 2470, 2530, 2560, 2590, 2480, 2450,
                  2500, 2540, 2610, 2580, 2490, 2460, 2520, 2550, 2590, 2600],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'Litros/día',
        'initials_variable': 'DH',
        'justification': 'Datos reales de ventas del último mes',
        'variable_name': 'demanda_historica'
    }, 
    {
        'answer': 2500,
        'question': '¿Cuál es la cantidad que produce diariamente en promedio?',
        'unit': 'Litros/día',
        'initials_variable': 'QPL',
        'justification': 'Producción actual promedio diaria',
        'variable_name': 'cantidad_producida_diaria'
    },
    {
        'answer': 2650,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'Litros/día',
        'initials_variable': 'DE',
        'justification': 'Proyección basada en tendencias históricas',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 15000,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'Litros',
        'initials_variable': 'CIP',
        'justification': 'Capacidad de almacenamiento de productos terminados',
        'variable_name': 'capacidad_inventario_productos'
    },
    {
        'answer': 'Sí',
        'question': '¿Existe estacionalidad en la demanda?',
        'initials_variable': 'ED',
        'justification': 'Mayor demanda en época escolar y festividades',
        'variable_name': 'estacionalidad_demanda'
    },
    {
        'answer': 8.20,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L',
        'initials_variable': 'CUIP',
        'justification': 'Costo de materia prima (leche cruda) por litro',
        'variable_name': 'costo_unitario_insumo_produccion'
    },
    {
        'answer': 2,
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'unit': 'días',
        'initials_variable': 'TPC',
        'justification': 'Frecuencia de compra de clientes regulares',
        'variable_name': 'tiempo_promedio_compras'
    },
    {
        'answer': 85,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'initials_variable': 'CPD',
        'justification': 'Promedio de clientes atendidos por día',
        'variable_name': 'clientes_por_dia'
    },
    {
        'answer': 15,
        'question': '¿Cuál es el número de empleados?',
        'unit': 'empleados',
        'initials_variable': 'NEPP',
        'justification': 'Personal total en producción',
        'variable_name': 'numero_empleados_produccion'
    },
    {
        'answer': 3000,
        'question': '¿Cuál es la capacidad de producción diaria?',
        'unit': 'Litros/día',
        'initials_variable': 'CPROD',
        'justification': 'Capacidad máxima de producción instalada',
        'variable_name': 'capacidad_produccion_diaria'
    },
    {
        'answer': 48000,
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'unit': 'Bs/mes',
        'initials_variable': 'SE',
        'justification': 'Planilla total mensual de empleados',
        'variable_name': 'sueldos_empleados'
    },
    {
        'answer': 15.80,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L',
        'initials_variable': 'PC',
        'justification': 'Estudio de precios de la competencia directa',
        'variable_name': 'precio_competencia'
    }, 
    {
        'answer': 1800,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'initials_variable': 'CFD',
        'justification': 'Costos fijos: alquiler, servicios básicos, seguros',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 0.35,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L',
        'initials_variable': 'CUTRANS',
        'justification': 'Costo de distribución por litro',
        'variable_name': 'costo_unitario_transporte'
    },
    {
        'answer': 3500,
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'unit': 'Bs/mes',
        'initials_variable': 'GMM',
        'justification': 'Inversión mensual en publicidad y promoción',
        'variable_name': 'gastos_marketing_mensuales'
    },
    {
        'answer': 3,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'initials_variable': 'TR',
        'justification': 'Frecuencia de compra de materia prima',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 1.05,
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'unit': 'L insumo/L producto',
        'initials_variable': 'CINSP',
        'justification': 'Factor de conversión insumo-producto',
        'variable_name': 'conversion_insumo_producto'
    },
    {
        'answer': 20000,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'Litros',
        'initials_variable': 'CMIPF',
        'justification': 'Capacidad total de almacén refrigerado',
        'variable_name': 'capacidad_maxima_inventario_productos_finales'
    }, 
    {
        'answer': 45,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/100L',
        'initials_variable': 'TPE',
        'justification': 'Tiempo de mano de obra por lote de 100L',
        'variable_name': 'tiempo_produccion_empleado'
    },
    {
        'answer': 500,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'Litros/lote',
        'initials_variable': 'CPPL',
        'justification': 'Tamaño estándar de lote de producción',
        'variable_name': 'cantidad_promedio_por_lote'
    },
    {
        'answer': 3000,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'unit': 'Litros',
        'initials_variable': 'SI',
        'justification': 'Inventario de seguridad para evitar roturas de stock',
        'variable_name': 'stock_inventario_seguridad'
    },
    {
        'answer': 3,
        'question': '¿Días promedio de reabastecimiento?',
        'unit': 'días',
        'initials_variable': 'DPL',
        'justification': 'Tiempo para reponer inventario desde pedido',
        'variable_name': 'dias_promedio_lead_time'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'unit': 'días',
        'initials_variable': 'TMP',
        'justification': 'Proceso ágil para pedidos pequeños',
        'variable_name': 'tiempo_medio_procesamiento'
    },
    {
        'answer': 200,
        'question': '¿Cuántos litros se transportan por viaje?',
        'unit': 'Litros/viaje',
        'initials_variable': 'CTPLV',
        'justification': 'Capacidad de transporte local',
        'variable_name': 'capacidad_transporte_por_viaje'
    },
    {
        'answer': 25,
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'unit': 'KM',
        'initials_variable': 'DPE',
        'justification': 'Distancia media de distribución urbana',
        'variable_name': 'distancia_promedio_entrega'
    },
    {
        'answer': 2800,
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'unit': 'Litros/día',
        'initials_variable': 'CTL',
        'justification': 'Consumo de leche cruda para producción',
        'variable_name': 'consumo_total_leche'
    },
    {
        'answer': 480,
        'question': '¿Cuántos minutos laborables tiene por día?',
        'unit': 'minutos',
        'initials_variable': 'MLP',
        'justification': 'Jornada laboral de 8 horas efectivas',
        'variable_name': 'minutos_laborables_por_dia'
    },
    {
        'answer': 30,
        'question': '¿Cuántos días máximos planea simular?',
        'unit': 'días',
        'initials_variable': 'NMD',
        'justification': 'Período de simulación de un mes',
        'variable_name': 'numero_maximo_dias'
    },
    {
        'answer': 3,
        'question': '¿Cuántos proveedores de leche tiene?',
        'unit': 'proveedores',
        'initials_variable': 'NPD',
        'justification': 'Red diversificada de proveedores locales',
        'variable_name': 'numero_proveedores_leche'
    },
    {
        'answer': 24,
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'unit': 'horas',
        'initials_variable': 'HTO',
        'justification': 'Operación continua con turnos',
        'variable_name': 'horas_totales_operacion'
    },
    {
        'answer': 3200,
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'unit': 'Litros',
        'initials_variable': 'QMAX',
        'justification': 'Capacidad teórica máxima al 100%',
        'variable_name': 'cantidad_maxima_producible'
    },
    {
        'answer': 4.0,
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'unit': '°C',
        'initials_variable': 'TCFO',
        'justification': 'Temperatura óptima para conservación láctea',
        'variable_name': 'temperatura_cadena_frio_objetivo'
    },
    {
        'answer': 0.5,
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'unit': 'horas',
        'initials_variable': 'TEO',
        'justification': 'Tiempo máximo aceptable de entrega',
        'variable_name': 'tiempo_entrega_objetivo'
    },
    {
        'answer': 2,
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'unit': 'días',
        'initials_variable': 'TE1',
        'justification': 'Lead time del proveedor más confiable',
        'variable_name': 'tiempo_entrega_proveedor_1'
    },
    {
        'answer': 3,
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'unit': 'días',
        'initials_variable': 'TE2',
        'justification': 'Lead time del segundo proveedor',
        'variable_name': 'tiempo_entrega_proveedor_2'
    },
    {
        'answer': 4,
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'unit': 'días',
        'initials_variable': 'TE3',
        'justification': 'Lead time del tercer proveedor',
        'variable_name': 'tiempo_entrega_proveedor_3'
    },
    {
        'answer': 0.5,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'unit': '%',
        'initials_variable': 'P1',
        'justification': '50% del suministro del proveedor principal',
        'variable_name': 'peso_proveedor_1'
    },
    {
        'answer': 0.3,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'unit': '%',
        'initials_variable': 'P2',
        'justification': '30% del suministro del proveedor secundario',
        'variable_name': 'peso_proveedor_2'
    },
    {
        'answer': 0.2,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'unit': '%',
        'initials_variable': 'P3',
        'justification': '20% del suministro del proveedor terciario',
        'variable_name': 'peso_proveedor_3'
    },
    {
        'answer': 35,
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'unit': '%',
        'initials_variable': 'PMC',
        'justification': 'Competidor líder con participación significativa',
        'variable_name': 'participacion_mercado_competidor'
    },
    {
        'answer': 12,
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'unit': 'productos',
        'initials_variable': 'NPC',
        'justification': 'Mercado con competencia moderada',
        'variable_name': 'numero_productos_competencia'
    }
]

# Respuestas específicas para Queso - COMPLETAS
answer_data_queso = [
    {
        'answer': 85.00,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/kg',
        'initials_variable': 'PVP',
        'justification': 'Precio de queso fresco tipo criollo',
        'variable_name': 'precio_actual'
    },    
    {
        'answer': [180, 175, 185, 190, 195, 170, 165, 188, 192, 186,
                  178, 182, 188, 194, 189, 176, 172, 185, 190, 187,
                  183, 179, 181, 186, 191, 188, 184, 180, 177, 185],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'kg/día',
        'initials_variable': 'DH',
        'justification': 'Producción de queso fresco último mes',
        'variable_name': 'demanda_historica'
    }, 
    {
        'answer': 185,
        'question': '¿Cuál es la cantidad producida diariamente?',
        'unit': 'kg/día',
        'initials_variable': 'QPL',
        'justification': 'Producción diaria promedio de queso',
        'variable_name': 'cantidad_producida_diaria'
    },
    {
        'answer': 200,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'kg/día',
        'initials_variable': 'DE',
        'justification': 'Demanda proyectada basada en crecimiento',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 1200,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'kg',
        'initials_variable': 'CIP',
        'justification': 'Capacidad de cámara frigorífica',
        'variable_name': 'capacidad_inventario_productos'
    },
    {
        'answer': 'No',
        'question': '¿Existe estacionalidad en la demanda?',
        'initials_variable': 'ED',
        'justification': 'Demanda constante durante el año',
        'variable_name': 'estacionalidad_demanda'
    },
    {
        'answer': 10.50,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L leche',
        'initials_variable': 'CUIP',
        'justification': 'Costo de leche para procesamiento',
        'variable_name': 'costo_unitario_insumo_produccion'
    },
    {
        'answer': 3,
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'unit': 'días',
        'initials_variable': 'TPC',
        'justification': 'Frecuencia de compra de distribuidores',
        'variable_name': 'tiempo_promedio_compras'
    },
    {
        'answer': 45,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'initials_variable': 'CPD',
        'justification': 'Clientes mayoristas y minoristas',
        'variable_name': 'clientes_por_dia'
    },
    {
        'answer': 25,
        'question': '¿Cuál es el número de empleados?',
        'unit': 'empleados',
        'initials_variable': 'NEPP',
        'justification': 'Personal especializado en quesería',
        'variable_name': 'numero_empleados_produccion'
    },
    {
        'answer': 250,
        'question': '¿Cuál es la capacidad de producción diaria?',
        'unit': 'kg/día',
        'initials_variable': 'CPROD',
        'justification': 'Capacidad máxima de planta quesera',
        'variable_name': 'capacidad_produccion_diaria'
    },
    {
        'answer': 87500,
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'unit': 'Bs/mes',
        'initials_variable': 'SE',
        'justification': 'Planilla mensual incluyendo maestros queseros',
        'variable_name': 'sueldos_empleados'
    },
    {
        'answer': 88.00,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/kg',
        'initials_variable': 'PC',
        'justification': 'Precio de mercado para queso similar',
        'variable_name': 'precio_competencia'
    }, 
    {
        'answer': 3200,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'initials_variable': 'CFD',
        'justification': 'Costos fijos de planta procesadora',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 2.50,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/kg',
        'initials_variable': 'CUTRANS',
        'justification': 'Transporte refrigerado por kg',
        'variable_name': 'costo_unitario_transporte'
    },
    {
        'answer': 5000,
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'unit': 'Bs/mes',
        'initials_variable': 'GMM',
        'justification': 'Marketing para posicionamiento de marca',
        'variable_name': 'gastos_marketing_mensuales'
    },
    {
        'answer': 2,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'initials_variable': 'TR',
        'justification': 'Recolección de leche cada 2 días',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 10.5,
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'unit': 'L leche/kg queso',
        'initials_variable': 'CINSP',
        'justification': 'Rendimiento típico leche-queso',
        'variable_name': 'conversion_insumo_producto'
    },
    {
        'answer': 1500,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'kg',
        'initials_variable': 'CMIPF',
        'justification': 'Capacidad total de maduración y almacén',
        'variable_name': 'capacidad_maxima_inventario_productos_finales'
    }, 
    {
        'answer': 120,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/10kg',
        'initials_variable': 'TPE',
        'justification': 'Tiempo de procesamiento manual intensivo',
        'variable_name': 'tiempo_produccion_empleado'
    },
    {
        'answer': 50,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'kg/lote',
        'initials_variable': 'CPPL',
        'justification': 'Lotes de queso por tanda',
        'variable_name': 'cantidad_promedio_por_lote'
    },
    {
        'answer': 200,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'unit': 'kg',
        'initials_variable': 'SI',
        'justification': 'Stock mínimo para cubrir demanda',
        'variable_name': 'stock_inventario_seguridad'
    },
    {
        'answer': 2,
        'question': '¿Días promedio de reabastecimiento?',
        'unit': 'días',
        'initials_variable': 'DPL',
        'justification': 'Lead time de materia prima',
        'variable_name': 'dias_promedio_lead_time'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'unit': 'días',
        'initials_variable': 'TMP',
        'justification': 'Procesamiento rápido por demanda B2B',
        'variable_name': 'tiempo_medio_procesamiento'
    },
    {
        'answer': 300,
        'question': '¿Cuántos litros se transportan por viaje?',
        'unit': 'kg/viaje',
        'initials_variable': 'CTPLV',
        'justification': 'Capacidad de vehículo refrigerado',
        'variable_name': 'capacidad_transporte_por_viaje'
    },
    {
        'answer': 40,
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'unit': 'KM',
        'initials_variable': 'DPE',
        'justification': 'Distribución regional para mayoristas',
        'variable_name': 'distancia_promedio_entrega'
    },
    {
        'answer': 2000,
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'unit': 'Litros/día',
        'initials_variable': 'CTL',
        'justification': 'Consumo de leche para producción de queso',
        'variable_name': 'consumo_total_leche'
    },
    {
        'answer': 480,
        'question': '¿Cuántos minutos laborables tiene por día?',
        'unit': 'minutos',
        'initials_variable': 'MLP',
        'justification': 'Jornada laboral estándar de 8 horas',
        'variable_name': 'minutos_laborables_por_dia'
    },
    {
        'answer': 30,
        'question': '¿Cuántos días máximos planea simular?',
        'unit': 'días',
        'initials_variable': 'NMD',
        'justification': 'Período de simulación mensual',
        'variable_name': 'numero_maximo_dias'
    },
    {
        'answer': 4,
        'question': '¿Cuántos proveedores de leche tiene?',
        'unit': 'proveedores',
        'initials_variable': 'NPD',
        'justification': 'Red de proveedores para asegurar calidad',
        'variable_name': 'numero_proveedores_leche'
    },
    {
        'answer': 16,
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'unit': 'horas',
        'initials_variable': 'HTO',
        'justification': 'Operación en dos turnos de trabajo',
        'variable_name': 'horas_totales_operacion'
    },
    {
        'answer': 280,
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'unit': 'kg',
        'initials_variable': 'QMAX',
        'justification': 'Capacidad máxima teórica de quesería',
        'variable_name': 'cantidad_maxima_producible'
    },
    {
        'answer': 3.5,
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'unit': '°C',
        'initials_variable': 'TCFO',
        'justification': 'Temperatura de maduración y conservación',
        'variable_name': 'temperatura_cadena_frio_objetivo'
    },
    {
        'answer': 1.0,
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'unit': 'horas',
        'initials_variable': 'TEO',
        'justification': 'Tiempo para distribución mayorista',
        'variable_name': 'tiempo_entrega_objetivo'
    },
    {
        'answer': 1,
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'unit': 'días',
        'initials_variable': 'TE1',
        'justification': 'Proveedor local muy cercano',
        'variable_name': 'tiempo_entrega_proveedor_1'
    },
    {
        'answer': 2,
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'unit': 'días',
        'initials_variable': 'TE2',
        'justification': 'Proveedor regional cercano',
        'variable_name': 'tiempo_entrega_proveedor_2'
    },
    {
        'answer': 3,
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'unit': 'días',
        'initials_variable': 'TE3',
        'justification': 'Proveedor de respaldo',
        'variable_name': 'tiempo_entrega_proveedor_3'
    },
    {
        'answer': 0.4,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'unit': '%',
        'initials_variable': 'P1',
        'justification': '40% del proveedor principal',
        'variable_name': 'peso_proveedor_1'
    },
    {
        'answer': 0.35,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'unit': '%',
        'initials_variable': 'P2',
        'justification': '35% del proveedor secundario',
        'variable_name': 'peso_proveedor_2'
    },
    {
        'answer': 0.25,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'unit': '%',
        'initials_variable': 'P3',
        'justification': '25% del proveedor terciario',
        'variable_name': 'peso_proveedor_3'
    },
    {
        'answer': 40,
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'unit': '%',
        'initials_variable': 'PMC',
        'justification': 'Competidor fuerte en el mercado quesero',
        'variable_name': 'participacion_mercado_competidor'
    },
    {
        'answer': 8,
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'unit': 'productos',
        'initials_variable': 'NPC',
        'justification': 'Mercado especializado con pocos competidores',
        'variable_name': 'numero_productos_competencia'
    }
]

# Respuestas específicas para Yogur - COMPLETAS
answer_data_yogur = [
    {
        'answer': 22.00,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'initials_variable': 'PVP',
        'justification': 'Precio premium por ser artesanal',
        'variable_name': 'precio_actual'
    },    
    {
        'answer': [320, 310, 330, 340, 335, 315, 325, 345, 350, 338,
                  322, 318, 332, 342, 336, 324, 320, 334, 344, 340,
                  328, 326, 330, 338, 346, 342, 334, 328, 322, 335],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'Litros/día',
        'initials_variable': 'DH',
        'justification': 'Ventas de yogur artesanal último mes',
        'variable_name': 'demanda_historica'
    }, 
    {
        'answer': 330,
        'question': '¿Cuál es la cantidad producida diariamente?',
        'unit': 'Litros/día',
        'initials_variable': 'QPL',
        'justification': 'Producción diaria de yogur natural',
        'variable_name': 'cantidad_producida_diaria'
    },
    {
        'answer': 380,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'Litros/día',
        'initials_variable': 'DE',
        'justification': 'Crecimiento esperado del mercado saludable',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 2500,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'Litros',
        'initials_variable': 'CIP',
        'justification': 'Capacidad de refrigeración para yogur',
        'variable_name': 'capacidad_inventario_productos'
    },
    {
        'answer': 'Sí',
        'question': '¿Existe estacionalidad en la demanda?',
        'initials_variable': 'ED',
        'justification': 'Mayor consumo en época calurosa',
        'variable_name': 'estacionalidad_demanda'
    },
    {
        'answer': 9.80,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L',
        'initials_variable': 'CUIP',
        'justification': 'Costo de leche más cultivos probióticos',
        'variable_name': 'costo_unitario_insumo_produccion'
    },
    {
        'answer': 1,
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'unit': 'días',
        'initials_variable': 'TPC',
        'justification': 'Consumo diario por ser producto saludable',
        'variable_name': 'tiempo_promedio_compras'
    },
    {
        'answer': 120,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'initials_variable': 'CPD',
        'justification': 'Clientela consciente de la salud',
        'variable_name': 'clientes_por_dia'
    },
    {
        'answer': 10,
        'question': '¿Cuál es el número de empleados?',
        'unit': 'empleados',
        'initials_variable': 'NEPP',
        'justification': 'Personal especializado en fermentación',
        'variable_name': 'numero_empleados_produccion'
    },
    {
        'answer': 400,
        'question': '¿Cuál es la capacidad de producción diaria?',
        'unit': 'Litros/día',
        'initials_variable': 'CPROD',
        'justification': 'Capacidad de fermentadores instalados',
        'variable_name': 'capacidad_produccion_diaria'
    },
    {
        'answer': 35000,
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'unit': 'Bs/mes',
        'initials_variable': 'SE',
        'justification': 'Planilla de empresa artesanal',
        'variable_name': 'sueldos_empleados'
    },
    {
        'answer': 20.00,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L',
        'initials_variable': 'PC',
        'justification': 'Precio de yogur industrial',
        'variable_name': 'precio_competencia'
    }, 
    {
        'answer': 1200,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'initials_variable': 'CFD',
        'justification': 'Costos fijos de planta artesanal',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 0.50,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L',
        'initials_variable': 'CUTRANS',
        'justification': 'Distribución local refrigerada',
        'variable_name': 'costo_unitario_transporte'
    },
    {
        'answer': 2500,
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'unit': 'Bs/mes',
        'initials_variable': 'GMM',
        'justification': 'Marketing enfocado en salud y bienestar',
        'variable_name': 'gastos_marketing_mensuales'
    },
    {
        'answer': 1,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'initials_variable': 'TR',
        'justification': 'Reabastecimiento diario por frescura',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 1.15,
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'unit': 'L insumo/L producto',
        'initials_variable': 'CINSP',
        'justification': 'Rendimiento de leche a yogur',
        'variable_name': 'conversion_insumo_producto'
    },
    {
        'answer': 3000,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'Litros',
        'initials_variable': 'CMIPF',
        'justification': 'Capacidad de cámaras de refrigeración',
        'variable_name': 'capacidad_maxima_inventario_productos_finales'
    }, 
    {
        'answer': 30,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/100L',
        'initials_variable': 'TPE',
        'justification': 'Tiempo de fermentación y envasado',
        'variable_name': 'tiempo_produccion_empleado'
    },
    {
        'answer': 100,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'Litros/lote',
        'initials_variable': 'CPPL',
        'justification': 'Lotes estándar de producción artesanal',
        'variable_name': 'cantidad_promedio_por_lote'
    },
    {
        'answer': 300,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'unit': 'Litros',
        'initials_variable': 'SI',
        'justification': 'Inventario mínimo para evitar faltantes',
        'variable_name': 'stock_inventario_seguridad'
    },
    {
        'answer': 1,
        'question': '¿Días promedio de reabastecimiento?',
        'unit': 'días',
        'initials_variable': 'DPL',
        'justification': 'Lead time corto por frescura del producto',
        'variable_name': 'dias_promedio_lead_time'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'unit': 'días',
        'initials_variable': 'TMP',
        'justification': 'Proceso ágil para pedidos pequeños',
        'variable_name': 'tiempo_medio_procesamiento'
    },
    {
        'answer': 200,
        'question': '¿Cuántos litros se transportan por viaje?',   
        'unit': 'Litros/viaje',
        'initials_variable': 'CTPLV',
        'justification': 'Capacidad de transporte local',
        'variable_name': 'capacidad_transporte_por_viaje'
    },
    {
        'answer': 20,
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'unit': 'KM',
        'initials_variable': 'DPE',
        'justification': 'Distribución local urbana',
        'variable_name': 'distancia_promedio_entrega'
    },
    {
        'answer': 380,
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'unit': 'Litros/día',
        'initials_variable': 'CTL',
        'justification': 'Consumo de leche para yogur',
        'variable_name': 'consumo_total_leche'
    },
    {
        'answer': 480,
        'question': '¿Cuántos minutos laborables tiene por día?',
        'unit': 'minutos',
        'initials_variable': 'MLP',
        'justification': 'Jornada artesanal de 8 horas',
        'variable_name': 'minutos_laborables_por_dia'
    },
    {
        'answer': 30,
        'question': '¿Cuántos días máximos planea simular?',
        'unit': 'días',
        'initials_variable': 'NMD',
        'justification': 'Simulación mensual',
        'variable_name': 'numero_maximo_dias'
    },
    {
        'answer': 2,
        'question': '¿Cuántos proveedores de leche tiene?',
        'unit': 'proveedores',
        'initials_variable': 'NPD',
        'justification': 'Proveedores locales de confianza',
        'variable_name': 'numero_proveedores_leche'
    },
    {
        'answer': 12,
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'unit': 'horas',
        'initials_variable': 'HTO',
        'justification': 'Operación diurna con fermentación nocturna',
        'variable_name': 'horas_totales_operacion'
    },
    {
        'answer': 420,
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'unit': 'Litros',
        'initials_variable': 'QMAX',
        'justification': 'Capacidad máxima de fermentadores',
        'variable_name': 'cantidad_maxima_producible'
    },
    {
        'answer': 4.5,
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'unit': '°C',
        'initials_variable': 'TCFO',
        'justification': 'Temperatura óptima para yogur',
        'variable_name': 'temperatura_cadena_frio_objetivo'
    },
    {
        'answer': 0.3,
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'unit': 'horas',
        'initials_variable': 'TEO',
        'justification': 'Entrega rápida local',
        'variable_name': 'tiempo_entrega_objetivo'
    },
    {
        'answer': 1,
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'unit': 'días',
        'initials_variable': 'TE1',
        'justification': 'Proveedor local diario',
        'variable_name': 'tiempo_entrega_proveedor_1'
    },
    {
        'answer': 2,
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'unit': 'días',
        'initials_variable': 'TE2',
        'justification': 'Proveedor de respaldo',
        'variable_name': 'tiempo_entrega_proveedor_2'
    },
    {
        'answer': 3,
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'unit': 'días',
        'initials_variable': 'TE3',
        'justification': 'Proveedor de emergencia',
        'variable_name': 'tiempo_entrega_proveedor_3'
    },
    {
        'answer': 0.7,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'unit': '%',
        'initials_variable': 'P1',
        'justification': '70% del proveedor principal',
        'variable_name': 'peso_proveedor_1'
    },
    {
        'answer': 0.2,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'unit': '%',
        'initials_variable': 'P2',
        'justification': '20% del proveedor secundario',
        'variable_name': 'peso_proveedor_2'
    },
    {
        'answer': 0.1,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'unit': '%',
        'initials_variable': 'P3',
        'justification': '10% del proveedor terciario',
        'variable_name': 'peso_proveedor_3'
    },
    {
        'answer': 25,
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'unit': '%',
        'initials_variable': 'PMC',
        'justification': 'Competencia moderada en yogur artesanal',
        'variable_name': 'participacion_mercado_competidor'
    },
    {
        'answer': 15,
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'unit': 'productos',
        'initials_variable': 'NPC',
        'justification': 'Mercado fragmentado con muchas opciones',
        'variable_name': 'numero_productos_competencia'
    }
]

# Respuestas específicas para Mantequilla
answer_data_mantequilla = [
    {
        'answer': 65.00,
        'question': '¿Cuál es el precio actual del producto?', 
        'unit': 'Bs/kg',
        'initials_variable': 'PVP',
        'justification': 'Precio de mantequilla artesanal premium',
        'variable_name': 'precio_actual'
    },
    {
        'answer': [75, 72, 78, 80, 77, 70, 74, 82, 79, 76,
                  73, 77, 81, 78, 75, 71, 76, 80, 83, 77,
                  74, 79, 82, 78, 75, 73, 77, 81, 79, 76],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'kg/día', 
        'initials_variable': 'DH',
        'justification': 'Registro de ventas diarias último mes',
        'variable_name': 'demanda_historica'
    },
    {
        'answer': 75,
        'question': '¿Cuál es la cantidad producida diariamente?',
        'unit': 'kg/día',
        'initials_variable': 'QPL',
        'justification': 'Producción diaria promedio',
        'variable_name': 'cantidad_producida_diaria'
    },
    {
        'answer': 85,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'kg/día',
        'initials_variable': 'DE', 
        'justification': 'Proyección basada en tendencia creciente',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 500,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'kg',
        'initials_variable': 'CIP',
        'justification': 'Capacidad de almacenamiento refrigerado',
        'variable_name': 'capacidad_inventario_productos'
    },
    {
        'answer': 'No',
        'question': '¿Existe estacionalidad en la demanda?',
        'initials_variable': 'ED',
        'justification': 'Demanda estable durante el año',
        'variable_name': 'estacionalidad_demanda'
    },
    {
        'answer': 12.50,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L crema',
        'initials_variable': 'CUIP',
        'justification': 'Costo de crema para batido',
        'variable_name': 'costo_unitario_insumo_produccion'
    },
    {
        'answer': 4,
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'unit': 'días',
        'initials_variable': 'TPC',
        'justification': 'Frecuencia típica de recompra',
        'variable_name': 'tiempo_promedio_compras'
    },
    {
        'answer': 35,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'initials_variable': 'CPD',
        'justification': 'Promedio de compradores diarios',
        'variable_name': 'clientes_por_dia'
    },
    {
        'answer': 8,
        'question': '¿Cuál es el número de empleados?',
        'unit': 'empleados',
        'initials_variable': 'NEPP',
        'justification': 'Personal de planta mantequillera',
        'variable_name': 'numero_empleados_produccion'
    },
    {
        'answer': 100,
        'question': '¿Cuál es la capacidad de producción diaria?',
        'unit': 'kg/día',
        'initials_variable': 'CPROD',
        'justification': 'Capacidad máxima instalada',
        'variable_name': 'capacidad_produccion_diaria'
    },
    {
        'answer': 28000,
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'unit': 'Bs/mes',
        'initials_variable': 'SE',
        'justification': 'Planilla mensual total',
        'variable_name': 'sueldos_empleados'
    },
    {
        'answer': 62.00,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/kg',
        'initials_variable': 'PC',
        'justification': 'Precio promedio del mercado',
        'variable_name': 'precio_competencia'
    },
    {
        'answer': 1500,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'initials_variable': 'CFD',
        'justification': 'Costos operativos fijos',
        'variable_name': 'costo_fijo_diario' 
    },
    {
        'answer': 1.80,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/kg',
        'initials_variable': 'CUTRANS',
        'justification': 'Costo logístico refrigerado',
        'variable_name': 'costo_unitario_transporte'
    },
    {
        'answer': 2000,
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'unit': 'Bs/mes',
        'initials_variable': 'GMM',
        'justification': 'Presupuesto promocional mensual',
        'variable_name': 'gastos_marketing_mensuales'
    },
    {
        'answer': 2,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'initials_variable': 'TR',
        'justification': 'Frecuencia de compra de crema',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 5.2,
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'unit': 'L crema/kg mantequilla',
        'initials_variable': 'CINSP',
        'justification': 'Ratio de conversión crema-mantequilla',
        'variable_name': 'conversion_insumo_producto'
    },
    {
        'answer': 600,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'kg',
        'initials_variable': 'CMIPF',
        'justification': 'Capacidad total de almacenamiento',
        'variable_name': 'capacidad_maxima_inventario_productos_finales'
    },
    {
        'answer': 90,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/10kg',
        'initials_variable': 'TPE',
        'justification': 'Tiempo de proceso por lote',
        'variable_name': 'tiempo_produccion_empleado'
    },
    {
        'answer': 25,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'kg/lote',
        'initials_variable': 'CPPL',
        'justification': 'Tamaño estándar de batida',
        'variable_name': 'cantidad_promedio_por_lote'
    },
    {
        'answer': 100,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'unit': 'kg',
        'initials_variable': 'SI',
        'justification': 'Stock mínimo requerido',
        'variable_name': 'stock_inventario_seguridad'
    },
    {
        'answer': 2,
        'question': '¿Días promedio de reabastecimiento?',
        'unit': 'días',
        'initials_variable': 'DPL',
        'justification': 'Lead time de materia prima',
        'variable_name': 'dias_promedio_lead_time'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'unit': 'días',
        'initials_variable': 'TMP',
        'justification': 'Tiempo de preparación de pedidos',
        'variable_name': 'tiempo_medio_procesamiento'
    },
    {
        'answer': 150,
        'question': '¿Cuántos litros se transportan por viaje?',
        'unit': 'kg/viaje',
        'initials_variable': 'CTPLV',
        'justification': 'Capacidad de reparto refrigerado',
        'variable_name': 'capacidad_transporte_por_viaje'
    },
    {
        'answer': 30,
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'unit': 'KM',
        'initials_variable': 'DPE',
        'justification': 'Distribución local y regional',
        'variable_name': 'distancia_promedio_entrega'
    },
    {
        'answer': 390,
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'unit': 'Litros/día',
        'initials_variable': 'CTL',
        'justification': 'Consumo de crema para mantequilla',
        'variable_name': 'consumo_total_leche'
    },
    {
        'answer': 480,
        'question': '¿Cuántos minutos laborables tiene por día?',
        'unit': 'minutos',
        'initials_variable': 'MLP',
        'justification': 'Jornada familiar de 8 horas',
        'variable_name': 'minutos_laborables_por_dia'
    },
    {
        'answer': 30,
        'question': '¿Cuántos días máximos planea simular?',
        'unit': 'días',
        'initials_variable': 'NMD',
        'justification': 'Simulación mensual',
        'variable_name': 'numero_maximo_dias'
    },
    {
        'answer': 2,
        'question': '¿Cuántos proveedores de leche tiene?',
        'unit': 'proveedores',
        'initials_variable': 'NPD',
        'justification': 'Proveedores familiares locales',
        'variable_name': 'numero_proveedores_leche'
    },
    {
        'answer': 10,
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'unit': 'horas',
        'initials_variable': 'HTO',
        'justification': 'Operación familiar diurna',
        'variable_name': 'horas_totales_operacion'
    },
    {
        'answer': 110,
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'unit': 'kg',
        'initials_variable': 'QMAX',
        'justification': 'Capacidad máxima de batidoras',
        'variable_name': 'cantidad_maxima_producible'
    },
    {
        'answer': 2.0,
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'unit': '°C',
        'initials_variable': 'TCFO',
        'justification': 'Temperatura para mantequilla sólida',
        'variable_name': 'temperatura_cadena_frio_objetivo'
    },
    {
        'answer': 0.8,
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'unit': 'horas',
        'initials_variable': 'TEO',
        'justification': 'Entrega local rápida',
        'variable_name': 'tiempo_entrega_objetivo'
    },
    {
        'answer': 2,
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'unit': 'días',
        'initials_variable': 'TE1',
        'justification': 'Proveedor local familiar',
        'variable_name': 'tiempo_entrega_proveedor_1'
    },
    {
        'answer': 3,
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'unit': 'días',
        'initials_variable': 'TE2',
        'justification': 'Proveedor de respaldo',
        'variable_name': 'tiempo_entrega_proveedor_2'
    },
    {
        'answer': 5,
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'unit': 'días',
        'initials_variable': 'TE3',
        'justification': 'Proveedor de emergencia',
        'variable_name': 'tiempo_entrega_proveedor_3'
    },
    {
        'answer': 0.6,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'unit': '%',
        'initials_variable': 'P1',
        'justification': '60% del proveedor principal',
        'variable_name': 'peso_proveedor_1'
    },
    {
        'answer': 0.4,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'unit': '%',
        'initials_variable': 'P2',
        'justification': '40% del proveedor secundario',
        'variable_name': 'peso_proveedor_2'
    },
    {
        'answer': 0.0,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'unit': '%',
        'initials_variable': 'P3',
        'justification': 'No usa tercer proveedor regularmente',
        'variable_name': 'peso_proveedor_3'
    },
    {
        'answer': 20,
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'unit': '%',
        'initials_variable': 'PMC',
        'justification': 'Mercado local con competencia baja',
        'variable_name': 'participacion_mercado_competidor'
    },
    {
        'answer': 6,
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'unit': 'productos',
        'initials_variable': 'NPC',
        'justification': 'Mercado pequeño con pocos competidores',
        'variable_name': 'numero_productos_competencia'
    }
]

# Respuestas específicas para Crema de Leche
answer_data_crema = [
    {
        'answer': 38.00,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'initials_variable': 'PVP',
        'justification': 'Precio competitivo para crema de leche fresca',
        'variable_name': 'precio_actual'
    },
    {
        'answer': [120, 115, 125, 122, 118, 128, 121, 119, 126, 124,
                  117, 123, 127, 120, 116, 122, 125, 118, 121, 124,
                  119, 126, 122, 117, 123, 120, 125, 121, 118, 124],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'L/día',
        'initials_variable': 'DH',
        'justification': 'Registro de ventas diarias último mes',
        'variable_name': 'demanda_historica'
    },
    {
        'answer': 120,
        'question': '¿Cuál es la cantidad producida diariamente?',
        'unit': 'L/día',
        'initials_variable': 'QPL',
        'justification': 'Producción diaria promedio actual',
        'variable_name': 'cantidad_producida_diaria'
    },
    {
        'answer': 150,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'L/día',
        'initials_variable': 'DE',
        'justification': 'Proyección de crecimiento mercado',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 800,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'L',
        'initials_variable': 'CIP',
        'justification': 'Capacidad de almacenamiento refrigerado',
        'variable_name': 'capacidad_inventario_productos'
    },
    {
        'answer': 'No',
        'question': '¿Existe estacionalidad en la demanda?',
        'initials_variable': 'ED',
        'justification': 'Demanda relativamente constante',
        'variable_name': 'estacionalidad_demanda'
    },
    {
        'answer': 11.20,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L leche',
        'initials_variable': 'CUIP',
        'justification': 'Costo de leche para descremado',
        'variable_name': 'costo_unitario_insumo_produccion'
    },
    {
        'answer': 3,
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'unit': 'días',
        'initials_variable': 'TPC',
        'justification': 'Frecuencia típica de recompra',
        'variable_name': 'tiempo_promedio_compras'
    },
    {
        'answer': 40,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'initials_variable': 'CPD',
        'justification': 'Promedio de clientes regulares',
        'variable_name': 'clientes_por_dia'
    },
    {
        'answer': 6,
        'question': '¿Cuál es el número de empleados?',
        'unit': 'empleados',
        'initials_variable': 'NEPP',
        'justification': 'Personal necesario para operación',
        'variable_name': 'numero_empleados_produccion'
    },
    {
        'answer': 180,
        'question': '¿Cuál es la capacidad de producción diaria?',
        'unit': 'L/día',
        'initials_variable': 'CPROD',
        'justification': 'Capacidad máxima de producción',
        'variable_name': 'capacidad_produccion_diaria'
    },
    {
        'answer': 21000,
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'unit': 'Bs/mes',
        'initials_variable': 'SE',
        'justification': 'Planilla mensual operativa',
        'variable_name': 'sueldos_empleados'
    },
    {
        'answer': 40.00,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L',
        'initials_variable': 'PC',
        'justification': 'Precio promedio mercado local',
        'variable_name': 'precio_competencia'
    },
    {
        'answer': 1000,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'initials_variable': 'CFD',
        'justification': 'Costos fijos operativos',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 0.80,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L',
        'initials_variable': 'CUTRANS',
        'justification': 'Costo de distribución refrigerada',
        'variable_name': 'costo_unitario_transporte'
    },
    {
        'answer': 1800,
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'unit': 'Bs/mes',
        'initials_variable': 'GMM',
        'justification': 'Presupuesto básico promocional',
        'variable_name': 'gastos_marketing_mensuales'
    },
    {
        'answer': 2,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'initials_variable': 'TR',
        'justification': 'Frecuencia de reposición',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 8.5,
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'unit': 'L leche/L crema',
        'initials_variable': 'CINSP',
        'justification': 'Ratio de conversión leche-crema',
        'variable_name': 'conversion_insumo_producto'
    },
    {
        'answer': 1000,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'L',
        'initials_variable': 'CMIPF',
        'justification': 'Capacidad total almacenamiento',
        'variable_name': 'capacidad_maxima_inventario_productos_finales'
    },
    {
        'answer': 45,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/100L',
        'initials_variable': 'TPE',
        'justification': 'Tiempo proceso descremado',
        'variable_name': 'tiempo_produccion_empleado'
    },
    {
        'answer': 40,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'L/lote',
        'initials_variable': 'CPPL',
        'justification': 'Tamaño estándar de lote',
        'variable_name': 'cantidad_promedio_por_lote'
    },
    {
        'answer': 80,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'unit': 'L',
        'initials_variable': 'SI',
        'justification': 'Stock mínimo necesario',
        'variable_name': 'stock_inventario_seguridad'
    },
    {
        'answer': 1,
        'question': '¿Días promedio de reabastecimiento?',
        'unit': 'días',
        'initials_variable': 'DPL',
        'justification': 'Lead time corto por frescura',
        'variable_name': 'dias_promedio_lead_time'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'unit': 'días',
        'initials_variable': 'TMP',
        'justification': 'Procesamiento ágil de pedidos',
        'variable_name': 'tiempo_medio_procesamiento'
    },
    {
        'answer': 100,
        'question': '¿Cuántos litros se transportan por viaje?',
        'unit': 'L/viaje',
        'initials_variable': 'CTPLV',
        'justification': 'Capacidad transporte refrigerado',
        'variable_name': 'capacidad_transporte_por_viaje'
    },
    {
        'answer': 15,
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'unit': 'KM',
        'initials_variable': 'DPE',
        'justification': 'Distribución muy local',
        'variable_name': 'distancia_promedio_entrega'
    },
    {
        'answer': 1020,
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'unit': 'Litros/día',
        'initials_variable': 'CTL',
        'justification': 'Consumo de leche para descremado',
        'variable_name': 'consumo_total_leche'
    },
    {
        'answer': 480,
        'question': '¿Cuántos minutos laborables tiene por día?',
        'unit': 'minutos',
        'initials_variable': 'MLP',
        'justification': 'Jornada de microempresa',
        'variable_name': 'minutos_laborables_por_dia'
    },
    {
        'answer': 30,
        'question': '¿Cuántos días máximos planea simular?',
        'unit': 'días',
        'initials_variable': 'NMD',
        'justification': 'Simulación mensual',
        'variable_name': 'numero_maximo_dias'
    },
    {
        'answer': 2,
        'question': '¿Cuántos proveedores de leche tiene?',
        'unit': 'proveedores',
        'initials_variable': 'NPD',
        'justification': 'Proveedores locales limitados',
        'variable_name': 'numero_proveedores_leche'
    },
    {
        'answer': 8,
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'unit': 'horas',
        'initials_variable': 'HTO',
        'justification': 'Operación diurna de microempresa',
        'variable_name': 'horas_totales_operacion'
    },
    {
        'answer': 200,
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'unit': 'Litros',
        'initials_variable': 'QMAX',
        'justification': 'Capacidad máxima teórica',
        'variable_name': 'cantidad_maxima_producible'
    },
    {
        'answer': 3.0,
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'unit': '°C',
        'initials_variable': 'TCFO',
        'justification': 'Temperatura para crema fresca',
        'variable_name': 'temperatura_cadena_frio_objetivo'
    },
    {
        'answer': 0.4,
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'unit': 'horas',
        'initials_variable': 'TEO',
        'justification': 'Entrega local muy rápida',
        'variable_name': 'tiempo_entrega_objetivo'
    },
    {
        'answer': 1,
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'unit': 'días',
        'initials_variable': 'TE1',
        'justification': 'Proveedor local diario',
        'variable_name': 'tiempo_entrega_proveedor_1'
    },
    {
        'answer': 2,
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'unit': 'días',
        'initials_variable': 'TE2',
        'justification': 'Proveedor alternativo',
        'variable_name': 'tiempo_entrega_proveedor_2'
    },
    {
        'answer': 4,
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'unit': 'días',
        'initials_variable': 'TE3',
        'justification': 'Proveedor de emergencia',
        'variable_name': 'tiempo_entrega_proveedor_3'
    },
    {
        'answer': 0.8,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'unit': '%',
        'initials_variable': 'P1',
        'justification': '80% del proveedor principal',
        'variable_name': 'peso_proveedor_1'
    },
    {
        'answer': 0.2,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'unit': '%',
        'initials_variable': 'P2',
        'justification': '20% del proveedor secundario',
        'variable_name': 'peso_proveedor_2'
    },
    {
        'answer': 0.0,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'unit': '%',
        'initials_variable': 'P3',
        'justification': 'No usa tercer proveedor',
        'variable_name': 'peso_proveedor_3'
    },
    {
        'answer': 15,
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'unit': '%',
        'initials_variable': 'PMC',
        'justification': 'Mercado local con baja competencia',
        'variable_name': 'participacion_mercado_competidor'
    },
    {
        'answer': 4,
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'unit': 'productos',
        'initials_variable': 'NPC',
        'justification': 'Mercado de nicho con pocos competidores',
        'variable_name': 'numero_productos_competencia'
    }
]

# Respuestas específicas para Leche Deslactosada
answer_data_leche_deslactosada = [
    {
        'answer': 18.50,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'initials_variable': 'PVP',
        'justification': 'Precio premium por proceso de deslactosado',
        'variable_name': 'precio_actual'
    },    
    {
        'answer': [1200, 1180, 1250, 1220, 1190, 1160, 1210, 1240, 1200, 1170,
                  1230, 1250, 1180, 1200, 1220, 1190, 1240, 1210, 1180, 1200,
                  1230, 1250, 1190, 1170, 1220, 1240, 1200, 1180, 1210, 1230],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'Litros/día',
        'initials_variable': 'DH',
        'justification': 'Registro ventas diarias último mes',
        'variable_name': 'demanda_historica'
    },
    {
        'answer': 1200,
        'question': '¿Cuál es la cantidad producida diariamente?',
        'unit': 'Litros/día', 
        'initials_variable': 'QPL',
        'justification': 'Producción actual promedio',
        'variable_name': 'cantidad_producida_diaria'
    },
    {
        'answer': 1500,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'Litros/día',
        'initials_variable': 'DE',
        'justification': 'Creciente demanda productos deslactosados',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 8000,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'Litros',
        'initials_variable': 'CIP',
        'justification': 'Capacidad almacenamiento refrigerado',
        'variable_name': 'capacidad_inventario_productos'
    },
    {
        'answer': 'No',
        'question': '¿Existe estacionalidad en la demanda?',
        'initials_variable': 'ED',
        'justification': 'Consumo constante todo el año',
        'variable_name': 'estacionalidad_demanda'
    },
    {
        'answer': 9.80,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L',
        'initials_variable': 'CUIP', 
        'justification': 'Costo leche más enzima lactasa',
        'variable_name': 'costo_unitario_insumo_produccion'
    },
    {
        'answer': 3,
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'unit': 'días',
        'initials_variable': 'TPC',
        'justification': 'Frecuencia compra habitual',
        'variable_name': 'tiempo_promedio_compras'
    },
    {
        'answer': 65,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'initials_variable': 'CPD',
        'justification': 'Clientes intolerantes a lactosa',
        'variable_name': 'clientes_por_dia'
    },
    {
        'answer': 12,
        'question': '¿Cuál es el número de empleados?',
        'unit': 'empleados',
        'initials_variable': 'NEPP',
        'justification': 'Personal especializado proceso deslactosado',
        'variable_name': 'numero_empleados_produccion'
    },
    {
        'answer': 1800,
        'question': '¿Cuál es la capacidad de producción diaria?',
        'unit': 'Litros/día',
        'initials_variable': 'CPROD',
        'justification': 'Capacidad máxima instalada',
        'variable_name': 'capacidad_produccion_diaria'
    },
    {
        'answer': 42000,
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'unit': 'Bs/mes',
        'initials_variable': 'SE',
        'justification': 'Planilla mensual empleados',
        'variable_name': 'sueldos_empleados'
    },
    {
        'answer': 19.20,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L',
        'initials_variable': 'PC',
        'justification': 'Precio promedio mercado local',
        'variable_name': 'precio_competencia'
    },
    {
        'answer': 1500,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'initials_variable': 'CFD',
        'justification': 'Costos fijos operación',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 0.40,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L',
        'initials_variable': 'CUTRANS',
        'justification': 'Costo distribución refrigerada',
        'variable_name': 'costo_unitario_transporte'
    },
    {
        'answer': 3000,
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'unit': 'Bs/mes',
        'initials_variable': 'GMM',
        'justification': 'Promoción beneficios deslactosados',
        'variable_name': 'gastos_marketing_mensuales'
    },
    {
        'answer': 2,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'initials_variable': 'TR',
        'justification': 'Frecuencia compra materia prima',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 1.10,
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'unit': 'L insumo/L producto',
        'initials_variable': 'CINSP',
        'justification': 'Factor conversión con mermas',
        'variable_name': 'conversion_insumo_producto'
    },
    {
        'answer': 10000,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'Litros',
        'initials_variable': 'CMIPF',
        'justification': 'Capacidad total almacén refrigerado',
        'variable_name': 'capacidad_maxima_inventario_productos_finales'
    },
    {
        'answer': 60,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/100L',
        'initials_variable': 'TPE',
        'justification': 'Tiempo proceso deslactosado',
        'variable_name': 'tiempo_produccion_empleado'
    },
    {
        'answer': 400,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'Litros/lote',
        'initials_variable': 'CPPL',
        'justification': 'Tamaño estándar lote',
        'variable_name': 'cantidad_promedio_por_lote'
    },
    {
        'answer': 1500,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'unit': 'Litros',
        'initials_variable': 'SI',
        'justification': 'Stock mínimo necesario',
        'variable_name': 'stock_inventario_seguridad'
    },
    {
        'answer': 2,
        'question': '¿Días promedio de reabastecimiento?',
        'unit': 'días', 
        'initials_variable': 'DPL',
        'justification': 'Lead time proveedores',
        'variable_name': 'dias_promedio_lead_time'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'unit': 'días',
        'initials_variable': 'TMP',
        'justification': 'Procesamiento eficiente pedidos',
        'variable_name': 'tiempo_medio_procesamiento'
    },
    {
        'answer': 180,
        'question': '¿Cuántos litros se transportan por viaje?',
        'unit': 'Litros/viaje',
        'initials_variable': 'CTPLV',
        'justification': 'Capacidad transporte refrigerado',
        'variable_name': 'capacidad_transporte_por_viaje'
    },
    {
        'answer': 35,
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'unit': 'KM',
        'initials_variable': 'DPE',
        'justification': 'Distribución regional especializada',
        'variable_name': 'distancia_promedio_entrega'
    },
    {
        'answer': 1320,
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'unit': 'Litros/día',
        'initials_variable': 'CTL',
        'justification': 'Consumo de leche para deslactosado',
        'variable_name': 'consumo_total_leche'
    },
    {
        'answer': 480,
        'question': '¿Cuántos minutos laborables tiene por día?',
        'unit': 'minutos',
        'initials_variable': 'MLP',
        'justification': 'Jornada especializada de 8 horas',
        'variable_name': 'minutos_laborables_por_dia'
    },
    {
        'answer': 30,
        'question': '¿Cuántos días máximos planea simular?',
        'unit': 'días',
        'initials_variable': 'NMD',
        'justification': 'Simulación mensual',
        'variable_name': 'numero_maximo_dias'
    },
    {
        'answer': 3,
        'question': '¿Cuántos proveedores de leche tiene?',
        'unit': 'proveedores',
        'initials_variable': 'NPD',
        'justification': 'Proveedores especializados',
        'variable_name': 'numero_proveedores_leche'
    },
    {
        'answer': 20,
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'unit': 'horas',
        'initials_variable': 'HTO',
        'justification': 'Operación en turnos especializados',
        'variable_name': 'horas_totales_operacion'
    },
    {
        'answer': 1900,
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'unit': 'Litros',
        'initials_variable': 'QMAX',
        'justification': 'Capacidad máxima de planta especializada',
        'variable_name': 'cantidad_maxima_producible'
    },
    {
        'answer': 4.0,
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'unit': '°C',
        'initials_variable': 'TCFO',
        'justification': 'Temperatura estándar láctea',
        'variable_name': 'temperatura_cadena_frio_objetivo'
    },
    {
        'answer': 0.6,
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'unit': 'horas',
        'initials_variable': 'TEO',
        'justification': 'Entrega especializada',
        'variable_name': 'tiempo_entrega_objetivo'
    },
    {
        'answer': 2,
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'unit': 'días',
        'initials_variable': 'TE1',
        'justification': 'Proveedor especializado cercano',
        'variable_name': 'tiempo_entrega_proveedor_1'
    },
    {
        'answer': 3,
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'unit': 'días',
        'initials_variable': 'TE2',
        'justification': 'Proveedor regional',
        'variable_name': 'tiempo_entrega_proveedor_2'
    },
    {
        'answer': 4,
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'unit': 'días',
        'initials_variable': 'TE3',
        'justification': 'Proveedor de respaldo',
        'variable_name': 'tiempo_entrega_proveedor_3'
    },
    {
        'answer': 0.5,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'unit': '%',
        'initials_variable': 'P1',
        'justification': '50% del proveedor principal',
        'variable_name': 'peso_proveedor_1'
    },
    {
        'answer': 0.3,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'unit': '%',
        'initials_variable': 'P2',
        'justification': '30% del proveedor secundario',
        'variable_name': 'peso_proveedor_2'
    },
    {
        'answer': 0.2,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'unit': '%',
        'initials_variable': 'P3',
        'justification': '20% del proveedor terciario',
        'variable_name': 'peso_proveedor_3'
    },
    {
        'answer': 45,
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'unit': '%',
        'initials_variable': 'PMC',
        'justification': 'Competidor fuerte en productos especializados',
        'variable_name': 'participacion_mercado_competidor'
    },
    {
        'answer': 5,
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'unit': 'productos',
        'initials_variable': 'NPC',
        'justification': 'Mercado especializado con pocos competidores',
        'variable_name': 'numero_productos_competencia'
    }
]

# Respuestas específicas para Dulce de Leche
answer_data_dulce_leche = [
    {
        'answer': 45.00,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/kg',
        'initials_variable': 'PVP',
        'justification': 'Precio competitivo para dulce de leche artesanal',
        'variable_name': 'precio_actual'
    },
    {
        'answer': [95, 92, 98, 94, 90, 96, 93, 97, 95, 91,
                  94, 96, 92, 95, 98, 93, 90, 95, 97, 94,
                  92, 96, 95, 91, 94, 98, 93, 95, 92, 96],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'kg/día',
        'initials_variable': 'DH',
        'justification': 'Registro de ventas diarias último mes',
        'variable_name': 'demanda_historica'
    },
    {
        'answer': 95,
        'question': '¿Cuál es la cantidad producida diariamente?',
        'unit': 'kg/día',
        'initials_variable': 'QPL',
        'justification': 'Producción diaria promedio actual',
        'variable_name': 'cantidad_producida_diaria'
    },
    {
        'answer': 120,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'kg/día',
        'initials_variable': 'DE',
        'justification': 'Proyección basada en tendencia creciente',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 600,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'kg',
        'initials_variable': 'CIP',
        'justification': 'Capacidad almacenamiento producto terminado',
        'variable_name': 'capacidad_inventario_productos'
    },
    {
        'answer': 'No',
        'question': '¿Existe estacionalidad en la demanda?',
        'initials_variable': 'ED',
        'justification': 'Consumo relativamente constante',
        'variable_name': 'estacionalidad_demanda'
    },
    {
        'answer': 8.50,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L leche',
        'initials_variable': 'CUIP',
        'justification': 'Costo de leche para procesamiento',
        'variable_name': 'costo_unitario_insumo_produccion'
    },
    {
        'answer': 5,
        'question': '¿Tiempo promedio entre compras de los clientes?',
        'unit': 'días',
        'initials_variable': 'TPC',
        'justification': 'Frecuencia típica de recompra',
        'variable_name': 'tiempo_promedio_compras'
    },
    {
        'answer': 30,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'initials_variable': 'CPD',
        'justification': 'Promedio de compradores diarios',
        'variable_name': 'clientes_por_dia'
    },
    {
        'answer': 8,
        'question': '¿Cuál es el número de empleados?',
        'unit': 'empleados',
        'initials_variable': 'NEPP',
        'justification': 'Personal dedicado a producción',
        'variable_name': 'numero_empleados_produccion'
    },
    {
        'answer': 150,
        'question': '¿Cuál es la capacidad de producción diaria?',
        'unit': 'kg/día',
        'initials_variable': 'CPROD',
        'justification': 'Capacidad máxima instalada',
        'variable_name': 'capacidad_produccion_diaria'
    },
    {
        'answer': 28000,
        'question': '¿Cuáles son los sueldos y salarios totales de los empleados?',
        'unit': 'Bs/mes',
        'initials_variable': 'SE',
        'justification': 'Planilla mensual total',
        'variable_name': 'sueldos_empleados'
    },
    {
        'answer': 42.00,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/kg',
        'initials_variable': 'PC',
        'justification': 'Precio promedio mercado local',
        'variable_name': 'precio_competencia'
    },
    {
        'answer': 1200,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'initials_variable': 'CFD',
        'justification': 'Costos fijos operativos',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 1.20,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/kg',
        'initials_variable': 'CUTRANS',
        'justification': 'Costo de distribución',
        'variable_name': 'costo_unitario_transporte'
    },
    {
        'answer': 2000,
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'unit': 'Bs/mes',
        'initials_variable': 'GMM',
        'justification': 'Presupuesto promocional mensual',
        'variable_name': 'gastos_marketing_mensuales'
    },
    {
        'answer': 3,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'initials_variable': 'TR',
        'justification': 'Frecuencia de reposición',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 3.5,
        'question': '¿Cuántos litros de insumo se utilizan para fabricar un litro de producto?',
        'unit': 'L leche/kg dulce',
        'initials_variable': 'CINSP',
        'justification': 'Ratio de conversión leche-dulce',
        'variable_name': 'conversion_insumo_producto'
    },
    {
        'answer': 800,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'kg',
        'initials_variable': 'CMIPF',
        'justification': 'Capacidad total almacenamiento',
        'variable_name': 'capacidad_maxima_inventario_productos_finales'
    },
    {
        'answer': 180,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/10kg',
        'initials_variable': 'TPE',
        'justification': 'Tiempo proceso cocción y batido',
        'variable_name': 'tiempo_produccion_empleado'
    },
    {
        'answer': 30,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'kg/lote',
        'initials_variable': 'CPPL',
        'justification': 'Tamaño estándar de lote',
        'variable_name': 'cantidad_promedio_por_lote'
    },
    {
        'answer': 100,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad?',
        'unit': 'kg',
        'initials_variable': 'SI',
        'justification': 'Stock mínimo necesario',
        'variable_name': 'stock_inventario_seguridad'
    },
    {
        'answer': 2,
        'question': '¿Días promedio de reabastecimiento?',
        'unit': 'días',
        'initials_variable': 'DPL',
        'justification': 'Lead time proveedores',
        'variable_name': 'dias_promedio_lead_time'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos?',
        'unit': 'días',
        'initials_variable': 'TMP',
        'justification': 'Procesamiento ágil pedidos',
        'variable_name': 'tiempo_medio_procesamiento'
    },
    {
        'answer': 120,
        'question': '¿Cuántos litros se transportan por viaje?',
        'unit': 'kg/viaje',
        'initials_variable': 'CTPLV',
        'justification': 'Capacidad transporte standard',
        'variable_name': 'capacidad_transporte_por_viaje'
    },
    {
        'answer': 22,
        'question': '¿Cuál es la distancia promedio de entrega a sus clientes?',
        'unit': 'KM',
        'initials_variable': 'DPE',
        'justification': 'Distribución tradicional local',
        'variable_name': 'distancia_promedio_entrega'
    },
    {
        'answer': 332,
        'question': '¿Cuál es el consumo diario promedio de materia prima?',
        'unit': 'Litros/día',
        'initials_variable': 'CTL',
        'justification': 'Consumo de leche para dulce',
        'variable_name': 'consumo_total_leche'
    },
    {
        'answer': 480,
        'question': '¿Cuántos minutos laborables tiene por día?',
        'unit': 'minutos',
        'initials_variable': 'MLP',
        'justification': 'Jornada tradicional de 8 horas',
        'variable_name': 'minutos_laborables_por_dia'
    },
    {
        'answer': 30,
        'question': '¿Cuántos días máximos planea simular?',
        'unit': 'días',
        'initials_variable': 'NMD',
        'justification': 'Simulación mensual',
        'variable_name': 'numero_maximo_dias'
    },
    {
        'answer': 2,
        'question': '¿Cuántos proveedores de leche tiene?',
        'unit': 'proveedores',
        'initials_variable': 'NPD',
        'justification': 'Proveedores tradicionales locales',
        'variable_name': 'numero_proveedores_leche'
    },
    {
        'answer': 12,
        'question': '¿Cuántas horas totales de operación tiene la planta por día?',
        'unit': 'horas',
        'initials_variable': 'HTO',
        'justification': 'Operación tradicional extendida',
        'variable_name': 'horas_totales_operacion'
    },
    {
        'answer': 160,
        'question': '¿Cuál es la cantidad máxima producible por día?',
        'unit': 'kg',
        'initials_variable': 'QMAX',
        'justification': 'Capacidad máxima de pailas',
        'variable_name': 'cantidad_maxima_producible'
    },
    {
        'answer': 18.0,
        'question': '¿Cuál es la temperatura objetivo para mantener la cadena de frío?',
        'unit': '°C',
        'initials_variable': 'TCFO',
        'justification': 'Temperatura ambiente controlada',
        'variable_name': 'temperatura_cadena_frio_objetivo'
    },
    {
        'answer': 1.0,
        'question': '¿Cuál es el tiempo objetivo de entrega por cliente?',
        'unit': 'horas',
        'initials_variable': 'TEO',
        'justification': 'Entrega tradicional pausada',
        'variable_name': 'tiempo_entrega_objetivo'
    },
    {
        'answer': 3,
        'question': '¿Cuántos días demora la entrega el proveedor principal?',
        'unit': 'días',
        'initials_variable': 'TE1',
        'justification': 'Proveedor tradicional local',
        'variable_name': 'tiempo_entrega_proveedor_1'
    },
    {
        'answer': 4,
        'question': '¿Cuántos días demora la entrega el proveedor secundario?',
        'unit': 'días',
        'initials_variable': 'TE2',
        'justification': 'Proveedor alternativo',
        'variable_name': 'tiempo_entrega_proveedor_2'
    },
    {
        'answer': 5,
        'question': '¿Cuántos días demora la entrega el proveedor terciario?',
        'unit': 'días',
        'initials_variable': 'TE3',
        'justification': 'Proveedor de emergencia',
        'variable_name': 'tiempo_entrega_proveedor_3'
    },
    {
        'answer': 0.7,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor principal?',
        'unit': '%',
        'initials_variable': 'P1',
        'justification': '70% del proveedor principal',
        'variable_name': 'peso_proveedor_1'
    },
    {
        'answer': 0.3,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor secundario?',
        'unit': '%',
        'initials_variable': 'P2',
        'justification': '30% del proveedor secundario',
        'variable_name': 'peso_proveedor_2'
    },
    {
        'answer': 0.0,
        'question': '¿Qué porcentaje de su materia prima le suministra el proveedor terciario?',
        'unit': '%',
        'initials_variable': 'P3',
        'justification': 'No usa tercer proveedor regularmente',
        'variable_name': 'peso_proveedor_3'
    },
    {
        'answer': 18,
        'question': '¿Cuál es la participación de mercado del principal competidor?',
        'unit': '%',
        'initials_variable': 'PMC',
        'justification': 'Mercado tradicional con baja competencia',
        'variable_name': 'participacion_mercado_competidor'
    },
    {
        'answer': 7,
        'question': '¿Cuántos productos competidores existen en el mercado?',
        'unit': 'productos',
        'initials_variable': 'NPC',
        'justification': 'Mercado tradicional con pocos competidores',
        'variable_name': 'numero_productos_competencia'
    }
]

# Función para generar datos más realistas
def get_realistic_answers(product_type):
    """Retorna respuestas realistas según el tipo de producto"""
    if product_type.lower() == 'leche':
        return answer_data_leche
    elif product_type.lower() == 'queso':
        return answer_data_queso
    elif product_type.lower() == 'yogur':
        return answer_data_yogur 
    elif product_type.lower() == 'mantequilla':
        return answer_data_mantequilla
    elif product_type.lower() == 'crema de Leche':
        return answer_data_crema
    elif product_type.lower() == 'leche deslactosada':
        return answer_data_leche_deslactosada
    elif product_type.lower() == 'dulce de leche':
        return answer_data_dulce_leche
    else:
        return []  # Respuestas genéricas si no se especifica producto