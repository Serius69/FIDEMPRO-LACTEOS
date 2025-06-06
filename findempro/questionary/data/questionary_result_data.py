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
        'answer': 15.50,  # Precio competitivo para leche en La Paz
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'justification': 'Precio basado en análisis de mercado local'
    },    
    {
        'answer': [2450, 2380, 2520, 2490, 2600, 2350, 2400, 2550, 2480, 2520,
                  2580, 2620, 2490, 2510, 2470, 2530, 2560, 2590, 2480, 2450,
                  2500, 2540, 2610, 2580, 2490, 2460, 2520, 2550, 2590, 2600],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'Litros/día',
        'justification': 'Datos reales de ventas del último mes'
    }, 
    {
        'answer': 2500,  # Producción diaria estable
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'unit': 'Litros/día'
    },
    {
        'answer': 2650,  # Demanda esperada ligeramente superior
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'Litros/día'
    },
    {
        'answer': 15000,  # Capacidad de tanques de almacenamiento
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'Litros'
    },
    {
        'answer': 'Sí',
        'question': '¿Existe estacionalidad en la demanda?',
        'justification': 'Mayor demanda en época escolar'
    },
    {
        'answer': 8.20,  # Costo de leche cruda
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L'
    },
    {
        'answer': 2,  # Compras cada 2 días
        'question': '¿Tiempo promedio entre compras?',
        'unit': 'días'
    },
    {
        'answer': 85,  # Clientes minoristas y mayoristas
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día'
    },
    {
        'answer': 15,
        'question': '¿Cuál es el numero de empleados?',
        'unit': 'empleados'
    },
    {
        'answer': 3000,  # Capacidad instalada
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'unit': 'Litros/día'
    },
    {
        'answer': 48000,  # Planilla mensual
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'unit': 'Bs/mes'
    },
    {
        'answer': 15.80,  # Precio de competencia
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L'
    }, 
    {
        'answer': 1800,  # Costos fijos diarios
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día'
    },
    {
        'answer': 0.35,  # Costo de transporte
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L'
    },
    {
        'answer': 3500,  # Marketing mensual
        'question': '¿Cuáles son los gastos de marketing?',
        'unit': 'Bs/mes'
    },
    {
        'answer': 3,  # Reabastecimiento cada 3 días
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días'
    },
    {
        'answer': 1.05,  # Solo leche cruda y aditivos
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'unit': 'L insumo/L producto'
    },
    {
        'answer': 20000,  # Capacidad de almacenamiento
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'Litros'
    }, 
    {
        'answer': 45,  # Tiempo de pasteurización y envasado
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/100L'
    },
    {
        'answer': 500,  # Lotes de 500 litros
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'Litros/lote'
    },
    {
        'answer': 3000,  # Stock de seguridad
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?',
        'unit': 'Litros'
    },
    {
        'answer': 3,  # Cada 3 días
        'question': '¿Dias promedio de reabastecimiento?',
        'unit': 'días'
    },
    {
        'answer': 1,  # 1 día para procesar pedidos
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?',
        'unit': 'días'
    },
    {
        'answer': 1500,  # Camión cisterna mediano
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?',
        'unit': 'Litros/viaje'
    },
    {
        'answer': 3,  # 3 proveedores locales
        'question': 'Número de Proveedores de Leche',
        'unit': 'proveedores'
    },
    {
        'answer': 2800,  # Consumo diario
        'question': '¿Cual es el consumo diario promedio de leche por proveedor?',
        'unit': 'Litros/día'
    },
]

# Respuestas específicas para Queso
answer_data_queso = [
    {
        'answer': 85.00,  # Precio de queso fresco
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/kg',
        'justification': 'Precio de queso fresco tipo criollo'
    },    
    {
        'answer': [180, 175, 185, 190, 195, 170, 165, 188, 192, 186,
                  178, 182, 188, 194, 189, 176, 172, 185, 190, 187,
                  183, 179, 181, 186, 191, 188, 184, 180, 177, 185],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'kg/día',
        'justification': 'Producción de queso fresco último mes'
    }, 
    {
        'answer': 185,  # Producción promedio
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'unit': 'kg/día'
    },
    {
        'answer': 200,  # Demanda creciente
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'kg/día'
    },
    {
        'answer': 1200,  # Cámara de maduración
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'kg'
    },
    {
        'answer': 'No',  # Demanda estable
        'question': '¿Existe estacionalidad en la demanda?',
        'justification': 'Demanda constante durante el año'
    },
    {
        'answer': 10.50,  # 10L leche = 1kg queso
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L leche'
    },
    {
        'answer': 3,  # Compras cada 3 días
        'question': '¿Tiempo promedio entre compras?',
        'unit': 'días'
    },
    {
        'answer': 45,  # Clientes mayoristas principalmente
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día'
    },
    {
        'answer': 25,  # Empresa mediana
        'question': '¿Cuál es el numero de empleados?',
        'unit': 'empleados'
    },
    {
        'answer': 250,  # Capacidad de producción
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'unit': 'kg/día'
    },
    {
        'answer': 87500,  # Planilla mensual
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'unit': 'Bs/mes'
    },
    {
        'answer': 88.00,  # Precio competencia
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/kg'
    }, 
    {
        'answer': 3200,  # Costos fijos mayores
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día'
    },
    {
        'answer': 2.50,  # Transporte refrigerado
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/kg'
    },
    {
        'answer': 5000,  # Marketing regional
        'question': '¿Cuáles son los gastos de marketing?',
        'unit': 'Bs/mes'
    },
    {
        'answer': 2,  # Reabastecimiento frecuente
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días'
    },
    {
        'answer': 10.5,  # Rendimiento quesero
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'unit': 'L leche/kg queso'
    },
    {
        'answer': 1500,  # Cámara refrigerada
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'kg'
    }, 
    {
        'answer': 120,  # Proceso más largo
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/10kg'
    },
    {
        'answer': 50,  # Lotes medianos
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'kg/lote'
    },
    {
        'answer': 200,  # Stock mínimo
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?',
        'unit': 'kg'
    },
    {
        'answer': 2,  # Cada 2 días
        'question': '¿Dias promedio de reabastecimiento?',
        'unit': 'días'
    },
    {
        'answer': 1,  # Procesamiento rápido
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?',
        'unit': 'días'
    },
    {
        'answer': 300,  # Camión pequeño
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?',
        'unit': 'kg/viaje'
    },
    {
        'answer': 4,  # Varios proveedores
        'question': 'Número de Proveedores de Leche',
        'unit': 'proveedores'
    },
    {
        'answer': 2000,  # Para producción quesera
        'question': '¿Cual es el consumo diario promedio de leche por proveedor?',
        'unit': 'Litros/día'
    },
]

# Respuestas específicas para Yogur
answer_data_yogur = [
    {
        'answer': 22.00,  # Precio yogur artesanal
        'question': '¿Cuál es el precio actual del producto?',
        'unit': 'Bs/L',
        'justification': 'Precio premium por ser artesanal'
    },    
    {
        'answer': [320, 310, 330, 340, 335, 315, 325, 345, 350, 338,
                  322, 318, 332, 342, 336, 324, 320, 334, 344, 340,
                  328, 326, 330, 338, 346, 342, 334, 328, 322, 335],
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'unit': 'Litros/día',
        'justification': 'Ventas de yogur artesanal último mes'
    }, 
    {
        'answer': 330,  # Producción actual
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'unit': 'Litros/día'
    },
    {
        'answer': 380,  # Demanda creciente
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'unit': 'Litros/día'
    },
    {
        'answer': 2500,  # Cámara refrigerada pequeña
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'unit': 'Litros'
    },
    {
        'answer': 'Sí',  # Mayor demanda en verano
        'question': '¿Existe estacionalidad en la demanda?',
        'justification': 'Mayor consumo en época calurosa'
    },
    {
        'answer': 9.80,  # Costo con cultivos y frutas
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'unit': 'Bs/L'
    },
    {
        'answer': 1,  # Compras diarias por frescura
        'question': '¿Tiempo promedio entre compras?',
        'unit': 'días'
    },
    {
        'answer': 120,  # Muchos clientes individuales
        'question': '¿Cuántos clientes llegan diariamente?',
        'unit': 'clientes/día'
    },
    {
        'answer': 10,  # Empresa pequeña
        'question': '¿Cuál es el numero de empleados?',
        'unit': 'empleados'
    },
    {
        'answer': 400,  # Capacidad limitada
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'unit': 'Litros/día'
    },
    {
        'answer': 35000,  # Planilla reducida
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'unit': 'Bs/mes'
    },
    {
        'answer': 20.00,  # Competencia industrial
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?',
        'unit': 'Bs/L'
    }, 
    {
        'answer': 1200,  # Costos fijos menores
        'question': '¿Cuál es el costo fijo diario?',
        'unit': 'Bs/día'
    },
    {
        'answer': 0.50,  # Distribución local
        'question': '¿Cuál es el costo unitario por transporte?',
        'unit': 'Bs/L'
    },
    {
        'answer': 2500,  # Marketing local
        'question': '¿Cuáles son los gastos de marketing?',
        'unit': 'Bs/mes'
    },
    {
        'answer': 1,  # Reabastecimiento diario
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'unit': 'días'
    },
    {
        'answer': 1.15,  # Leche, cultivos y frutas
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'unit': 'L insumo/L producto'
    },
    {
        'answer': 3000,  # Almacenamiento limitado
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'unit': 'Litros'
    }, 
    {
        'answer': 90,  # Proceso con fermentación
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?',
        'unit': 'minutos/50L'
    },
    {
        'answer': 100,  # Lotes pequeños
        'question': '¿Cuánto es la cantidad promedio producida por lote?',
        'unit': 'Litros/lote'
    },
    {
        'answer': 400,  # Stock mínimo
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?',
        'unit': 'Litros'
    },
    {
        'answer': 1,  # Diario por frescura
        'question': '¿Dias promedio de reabastecimiento?',
        'unit': 'días'
    },
    {
        'answer': 0.5,  # Medio día
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?',
        'unit': 'días'
    },
    {
        'answer': 200,  # Vehículo pequeño
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?',
        'unit': 'Litros/viaje'
    },
    {
        'answer': 2,  # Proveedores locales
        'question': 'Número de Proveedores de Leche',
        'unit': 'proveedores'
    },
    {
        'answer': 400,  # Consumo menor
        'question': '¿Cual es el consumo diario promedio de leche por proveedor?',
        'unit': 'Litros/día'
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
        return answer_data  # Respuestas genéricas si no se especifica producto

# Respuestas genéricas para casos no especificados
answer_data = [
    {
        'answer': random.randint(15, 25),  
        'question': '¿Cuál es el precio actual del producto?'
    },    
    {
        'answer': np.random.normal(loc=2500.0, scale=250.0, size=30).tolist(),
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).'
    }, 
    {
        'answer': random.randint(200, 500),
        'question': '¿Cuántos productos están siendo producidos actualmente?'
    },
    {
        'answer': random.randint(250, 600), 
        'question': '¿Cuál es la demanda esperada para los productos lácteos?'
    },
    {
        'answer': random.randint(1000, 5000),
        'question': '¿Cuál es la capacidad del inventario de productos?'
    },
    {
        'answer': random.choice(['Sí', 'No']),
        'question': '¿Existe estacionalidad en la demanda?'
    },
    {
        'answer': round(random.uniform(5.0, 15.0), 2),
        'question': '¿Cuál es el costo unitario del insumo para la producción?'
    },
    {
        'answer': random.randint(1, 7),
        'question': '¿Tiempo promedio entre compras?'
    },
    {
        'answer': random.randint(50, 150),
        'question': '¿Cuántos clientes llegan diariamente?'
    },
    {
        'answer': random.randint(10, 30),
        'question': '¿Cuál es el numero de empleados?'
    },
    {
        'answer': random.randint(500, 2000),
        'question': '¿Cuál es el nivel de capacidad de producción?'
    },
    {
        'answer': random.randint(30000, 100000),
        'question': '¿Cuáles son los sueldos y salarios de los empleados?'
    },
    {
        'answer': round(random.uniform(15, 30), 2),
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?'
    }, 
    {
        'answer': random.randint(1000, 3000),
        'question': '¿Cuál es el costo fijo diario?'
    },
    {
        'answer': round(random.uniform(0.3, 1.5), 2),
        'question': '¿Cuál es el costo unitario por transporte?'
    },
    {
        'answer': random.randint(2000, 6000), 
        'question': '¿Cuáles son los gastos de marketing?'
    },
    {
        'answer': random.randint(1, 7),
        'question': '¿Cada cuánto tiempo se reabastece de insumos?'
    },
    {
        'answer': round(random.uniform(1.0, 2.0), 2),
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?'
    },
    {
        'answer': random.randint(2000, 10000),
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?'
    }, 
    {
        'answer': random.randint(30, 120),
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?'
    },
    {
        'answer': random.randint(100, 500),
        'question': '¿Cuánto es la cantidad promedio producida por lote ?'
    },
    {
        'answer': random.randint(500, 2000),
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?'
    },
    {
        'answer': random.randint(1, 5),
        'question': '¿Dias promedio de reabastecimiento?'
    },
    {
        'answer': round(random.uniform(0.5, 2.0), 1),
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?'
    },
    {
        'answer': random.randint(500, 2000),
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?'
    },
    {
        'answer': random.randint(500, 2000),
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?'
    },
    {
        'answer': random.randint(2, 5),
        'question': 'Número de Proveedores de Leche'
    },
    {
        'answer': random.randint(1000, 3000),
        'question': '¿Cual es el consumo diario promedio de leche por proveedor?'
    },
]