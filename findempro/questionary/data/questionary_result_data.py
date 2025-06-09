# questionary_result_data.py - Versión Final
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
]

# Respuestas específicas para Leche
answer_data_leche = [
    {
        'answer': 15.50,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'justification': 'Precio basado en análisis de mercado local',
        'variable_name': 'precio_actual'  # Nombre de la variable en tu modelo Variable
    },    
    {
        'answer': [2450, 2380, 2520, 2490, 2600, 2350, 2400, 2550, 2480, 2520,
                  2580, 2620, 2490, 2510, 2470, 2530, 2560, 2590, 2480, 2450,
                  2500, 2540, 2610, 2580, 2490, 2460, 2520, 2550, 2590, 2600],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'Litros/día',
        'justification': 'Datos reales de ventas del último mes',
        'variable_name': 'demanda_historica'
    }, 
    {
        'answer': 2500,
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'unit': 'Litros/día',
        'variable_name': 'produccion_actual'
    },
    {
        'answer': 2650,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'Litros/día',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 15000,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'Litros',
        'variable_name': 'capacidad_inventario'
    },
    {
        'answer': 'Sí',
        'question': '¿Existe estacionalidad en la demanda?',
        'justification': 'Mayor demanda en época escolar',
        'variable_name': 'estacionalidad'
    },
    {
        'answer': 8.20,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L',
        'variable_name': 'costo_unitario_insumo'
    },
    {
        'answer': 2,
        'question': '¿Tiempo promedio entre compras?',
        'unit': 'días',
        'variable_name': 'tiempo_entre_compras'
    },
    {
        'answer': 85,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'variable_name': 'clientes_diarios'
    },
    {
        'answer': 15,
        'question': '¿Cuál es el numero de empleados?',
        'unit': 'empleados',
        'variable_name': 'numero_empleados'
    },
    {
        'answer': 3000,
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'unit': 'Litros/día',
        'variable_name': 'capacidad_produccion'
    },
    {
        'answer': 48000,
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'unit': 'Bs/mes',
        'variable_name': 'sueldos_salarios'
    },
    {
        'answer': 15.80,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L',
        'variable_name': 'precio_competencia'
    }, 
    {
        'answer': 1800,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 0.35,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L',
        'variable_name': 'costo_transporte'
    },
    {
        'answer': 3500,
        'question': '¿Cuáles son los gastos de marketing?',
        'unit': 'Bs/mes',
        'variable_name': 'gastos_marketing'
    },
    {
        'answer': 3,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 1.05,
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'unit': 'L insumo/L producto',
        'variable_name': 'insumos_por_producto'
    },
    {
        'answer': 20000,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'Litros',
        'variable_name': 'capacidad_almacenamiento'
    }, 
    {
        'answer': 45,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/100L',
        'variable_name': 'tiempo_produccion_unitario'
    },
    {
        'answer': 500,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'Litros/lote',
        'variable_name': 'cantidad_por_lote'
    },
    {
        'answer': 3000,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?',
        'unit': 'Litros',
        'variable_name': 'stock_seguridad'
    },
    {
        'answer': 3,
        'question': '¿Dias promedio de reabastecimiento?',
        'unit': 'días',
        'variable_name': 'dias_reabastecimiento'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?',
        'unit': 'días',
        'variable_name': 'tiempo_procesamiento_pedidos'
    },
    {
        'answer': 1500,
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?',
        'unit': 'Litros/viaje',
        'variable_name': 'cantidad_transporte_viaje'
    },
    {
        'answer': 3,
        'question': 'Número de Proveedores de Leche',
        'unit': 'proveedores',
        'variable_name': 'numero_proveedores'
    },
    {
        'answer': 2800,
        'question': '¿Cual es el consumo diario promedio de leche por proveedor?',
        'unit': 'Litros/día',
        'variable_name': 'consumo_diario_proveedor'
    },
]

# Respuestas específicas para Queso
answer_data_queso = [
    {
        'answer': 85.00,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/kg',
        'justification': 'Precio de queso fresco tipo criollo',
        'variable_name': 'precio_actual'
    },    
    {
        'answer': [180, 175, 185, 190, 195, 170, 165, 188, 192, 186,
                  178, 182, 188, 194, 189, 176, 172, 185, 190, 187,
                  183, 179, 181, 186, 191, 188, 184, 180, 177, 185],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'kg/día',
        'justification': 'Producción de queso fresco último mes',
        'variable_name': 'demanda_historica'
    }, 
    {
        'answer': 185,
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'unit': 'kg/día',
        'variable_name': 'produccion_actual'
    },
    {
        'answer': 200,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'kg/día',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 1200,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'kg',
        'variable_name': 'capacidad_inventario'
    },
    {
        'answer': 'No',
        'question': '¿Existe estacionalidad en la demanda?',
        'justification': 'Demanda constante durante el año',
        'variable_name': 'estacionalidad'
    },
    {
        'answer': 10.50,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L leche',
        'variable_name': 'costo_unitario_insumo'
    },
    {
        'answer': 3,
        'question': '¿Tiempo promedio entre compras?',
        'unit': 'días',
        'variable_name': 'tiempo_entre_compras'
    },
    {
        'answer': 45,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'variable_name': 'clientes_diarios'
    },
    {
        'answer': 25,
        'question': '¿Cuál es el numero de empleados?',
        'unit': 'empleados',
        'variable_name': 'numero_empleados'
    },
    {
        'answer': 250,
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'unit': 'kg/día',
        'variable_name': 'capacidad_produccion'
    },
    {
        'answer': 87500,
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'unit': 'Bs/mes',
        'variable_name': 'sueldos_salarios'
    },
    {
        'answer': 88.00,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/kg',
        'variable_name': 'precio_competencia'
    }, 
    {
        'answer': 3200,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 2.50,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/kg',
        'variable_name': 'costo_transporte'
    },
    {
        'answer': 5000,
        'question': '¿Cuáles son los gastos de marketing?',
        'unit': 'Bs/mes',
        'variable_name': 'gastos_marketing'
    },
    {
        'answer': 2,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 10.5,
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'unit': 'L leche/kg queso',
        'variable_name': 'insumos_por_producto'
    },
    {
        'answer': 1500,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'kg',
        'variable_name': 'capacidad_almacenamiento'
    }, 
    {
        'answer': 120,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/10kg',
        'variable_name': 'tiempo_produccion_unitario'
    },
    {
        'answer': 50,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'kg/lote',
        'variable_name': 'cantidad_por_lote'
    },
    {
        'answer': 200,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?',
        'unit': 'kg',
        'variable_name': 'stock_seguridad'
    },
    {
        'answer': 2,
        'question': '¿Dias promedio de reabastecimiento?',
        'unit': 'días',
        'variable_name': 'dias_reabastecimiento'
    },
    {
        'answer': 1,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?',
        'unit': 'días',
        'variable_name': 'tiempo_procesamiento_pedidos'
    },
    {
        'answer': 300,
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?',
        'unit': 'kg/viaje',
        'variable_name': 'cantidad_transporte_viaje'
    },
    {
        'answer': 4,
        'question': 'Número de Proveedores de Leche',
        'unit': 'proveedores',
        'variable_name': 'numero_proveedores'
    },
    {
        'answer': 2000,
        'question': '¿Cual es el consumo diario promedio de leche por proveedor?',
        'unit': 'Litros/día',
        'variable_name': 'consumo_diario_proveedor'
    },
]

# Respuestas específicas para Yogur
answer_data_yogur = [
    {
        'answer': 22.00,
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'justification': 'Precio premium por ser artesanal',
        'variable_name': 'precio_actual'
    },    
    {
        'answer': [320, 310, 330, 340, 335, 315, 325, 345, 350, 338,
                  322, 318, 332, 342, 336, 324, 320, 334, 344, 340,
                  328, 326, 330, 338, 346, 342, 334, 328, 322, 335],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'Litros/día',
        'justification': 'Ventas de yogur artesanal último mes',
        'variable_name': 'demanda_historica'
    }, 
    {
        'answer': 330,
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'unit': 'Litros/día',
        'variable_name': 'produccion_actual'
    },
    {
        'answer': 380,
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'Litros/día',
        'variable_name': 'demanda_esperada'
    },
    {
        'answer': 2500,
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'Litros',
        'variable_name': 'capacidad_inventario'
    },
    {
        'answer': 'Sí',
        'question': '¿Existe estacionalidad en la demanda?',
        'justification': 'Mayor consumo en época calurosa',
        'variable_name': 'estacionalidad'
    },
    {
        'answer': 9.80,
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L',
        'variable_name': 'costo_unitario_insumo'
    },
    {
        'answer': 1,
        'question': '¿Tiempo promedio entre compras?',
        'unit': 'días',
        'variable_name': 'tiempo_entre_compras'
    },
    {
        'answer': 120,
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día',
        'variable_name': 'clientes_diarios'
    },
    {
        'answer': 10,
        'question': '¿Cuál es el numero de empleados?',
        'unit': 'empleados',
        'variable_name': 'numero_empleados'
    },
    {
        'answer': 400,
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'unit': 'Litros/día',
        'variable_name': 'capacidad_produccion'
    },
    {
        'answer': 35000,
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'unit': 'Bs/mes',
        'variable_name': 'sueldos_salarios'
    },
    {
        'answer': 20.00,
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L',
        'variable_name': 'precio_competencia'
    }, 
    {
        'answer': 1200,
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día',
        'variable_name': 'costo_fijo_diario'
    },
    {
        'answer': 0.50,
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L',
        'variable_name': 'costo_transporte'
    },
    {
        'answer': 2500,
        'question': '¿Cuáles son los gastos de marketing?',
        'unit': 'Bs/mes',
        'variable_name': 'gastos_marketing'
    },
    {
        'answer': 1,
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días',
        'variable_name': 'tiempo_reabastecimiento'
    },
    {
        'answer': 1.15,
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'unit': 'L insumo/L producto',
        'variable_name': 'insumos_por_producto'
    },
    {
        'answer': 3000,
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'Litros',
        'variable_name': 'capacidad_almacenamiento'
    }, 
    {
        'answer': 90,
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/50L',
        'variable_name': 'tiempo_produccion_unitario'
    },
    {
        'answer': 100,
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'Litros/lote',
        'variable_name': 'cantidad_por_lote'
    },
    {
        'answer': 400,
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?',
        'unit': 'Litros',
        'variable_name': 'stock_seguridad'
    },
    {
        'answer': 1,
        'question': '¿Dias promedio de reabastecimiento?',
        'unit': 'días',
        'variable_name': 'dias_reabastecimiento'
    },
    {
        'answer': 0.5,
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?',
        'unit': 'días',
        'variable_name': 'tiempo_procesamiento_pedidos'
    },
    {
        'answer': 200,
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?',
        'unit': 'Litros/viaje',
        'variable_name': 'cantidad_transporte_viaje'
    },
    {
        'answer': 2,
        'question': 'Número de Proveedores de Leche',
        'unit': 'proveedores',
        'variable_name': 'numero_proveedores'
    },
    {
        'answer': 400,
        'question': '¿Cual es el consumo diario promedio de leche por proveedor?',
        'unit': 'Litros/día',
        'variable_name': 'consumo_diario_proveedor'
    },
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
    else:
        return []  # Respuestas genéricas si no se especifica producto
    
    
