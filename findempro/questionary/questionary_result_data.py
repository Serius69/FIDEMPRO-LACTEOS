import random
import numpy as np
questionary_result_data = [
    {
    'name': 'Respuestas para el producto Leche',
    },
    {
    'name': 'Respuestas para el producto Queso',
    },
    {
    'name': 'Respuestas para el producto Yogur',
    },
    ]
answer_data = [
    {
        'answer': random.randint(5, 15),  
        'question': '¿Cuál es el precio actual del producto?'
    },    
    {
        # 'answer': [random.randint(100, 1000) for i in range(30)],
        'answer': np.random.normal(loc=2500.0, scale=10.0, size=30),
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).'
    }, 
    {
        'answer': random.randint(50, 300),
        'question': '¿Cuántos productos están siendo producidos actualmente?'
    },
    {
        'answer': random.randint(100, 1000), 
        'question': '¿Cuál es la demanda esperada para los productos lácteos?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuál es la capacidad del inventario de productos?'
    },
    {
        'answer': random.choice(['Sí', 'No']),
        'question': '¿Existe estacionalidad en la demanda?'
    },
    {
        'answer': round(random.uniform(0.2, 2), 2),
        'question': '¿Cuál es el costo unitario del insumo para la producción?'
    },
    
    {
        'answer': random.randint(1, 10),
        'question': '¿Tiempo promedio entre compras?'
    },
    {
        'answer': random.randint(50, 500),
        'question': '¿Cuántos clientes llegan diariamente?'
    },
    {
        'answer': random.randint(50, 100),
        'question': '¿Cuál es el numero de empleados?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuál es el nivel de capacidad de producción?'
    },
    {
        'answer': random.randint(1000, 10000),
        'question': '¿Cuáles son los sueldos y salarios de los empleados?'
    },
    {
        'answer': round(random.uniform(10, 20), 2),
        'question': '¿Cuál es el precio promedio actual de los productos lácteos de la competencia?'
    }, 
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuál es el costo fijo diario?'
    },
    {
        'answer': round(random.uniform(0.1, 1), 2),
        'question': '¿Cuál es el costo unitario por transporte?'
    },
    {
        'answer': random.randint(100, 1000), 
        'question': '¿Cuáles son los gastos de marketing?'
    },
    {
        'answer': random.randint(3, 10),
        'question': '¿Cada cuánto tiempo se reabastece de insumos?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?'
    }, 
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuánto es la cantidad promedio producida por lote ?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuál es el stock de inventario mínimo de seguridad (SI) para la capacidad máxima de insumos del producto final, medido en días?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Dias promedio de reabastecimiento?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuál es el tiempo medio de procesamiento de pedidos (TMP) actual en dias?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuántos litros, en promedio, se transportan por viaje según la variable Cantidad transportada por viaje?'
    },
    {
        'answer': random.randint(1, 3),
        'question': 'Número de Proveedores de Leche'
    },
]
    