questionary_result_data = [
    
    {
    'name': 'Leche',
    },
    {
    'name': 'Queso',
    },
    {
    'name': 'Yogurt',
    },
    ]

import random

answer_data = [
    {
        'answer': random.randint(100, 500),  
        'question': '¿Cuántos productos lácteos vende diariamente?'
    },
    {
        'answer': round(random.uniform(1, 5), 2),
        'question': '¿Cuál es el precio actual de sus productos lácteos?'
    },
    {
        'answer': [random.randint(100, 1000) for i in range(30)],
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
        'answer': round(random.uniform(0.5, 3), 2),
        'question': '¿Cuál es el costo unitario de producción?'
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
        'answer': random.choice(['Muy competitivo', 'Medianamente competitivo', 'Poco competitivo']),
        'question': '¿Cuál es el nivel de competitividad en el mercado de su empresa?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cómo se posiciona su empresa en el mercado?'
    },
    {
        'answer': random.choice(['Diaria','Semanal','Quincenal','Mensual']), 
        'question': '¿Con qué frecuencia compran los clientes?'
    },
    {
        'answer': round(random.uniform(0.1, 0.9), 2),
        'question': '¿Cuál es la tasa de retención de clientes de su empresa?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuál es el nivel de satisfacción del cliente?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuál es el nivel de lealtad del cliente?'
    },
    {
        'answer': round(random.uniform(5, 50), 2),
        'question': '¿Cuánto cuesta adquirir un nuevo cliente?'
    },
    {
        'answer': round(random.uniform(1, 20), 2),
        'question': '¿Cuánto cuesta retener a un cliente?'
    },
    {
        'answer': random.randint(50, 500),
        'question': '¿Cuántos clientes llegan diariamente?'
    },
    {
        'answer': random.choice(['Totalmente automatizado', 'Parcialmente automatizado', 'Manual']),
        'question': '¿Cuál es el nivel de automatización del proceso de producción?'
    },
    {
        'answer': random.randint(1, 10), 
        'question': '¿Cuál es el nivel de eficiencia del proceso de producción?'
    },
    {
        'answer': random.choice(['ISO 9001', 'HACCP','Ninguna', 'Otras (especificar)']),
        'question': '¿La empresa cuenta con certificaciones de calidad?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuánto tiempo tarda en producir un producto?'
    },
    {
        'answer': random.randint(100, 1000),
        'question': '¿Cuál es el nivel de capacidad de producción?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuál es el nivel de flexibilidad en la producción?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuál es el nivel de eficiencia del inventario?'
    },
    {
        'answer': random.randint(1, 10), 
        'question': '¿Cuál es el nivel de eficiencia en la cadena de suministro?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuál es el nivel de eficiencia en la gestión de compra de insumos?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuál es el nivel de eficiencia en la gestión de ventas?'
    },
    {
        'answer': random.randint(1000, 10000),
        'question': '¿Cuáles son los sueldos y salarios de los empleados?'
    },
    {
        'answer': round(random.uniform(1, 5), 2),
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
        'answer': round(random.uniform(0.1, 1), 2), 
        'question': '¿Cuál es el costo unitario del inventario?'
    },
    {
        'answer': random.randint(100, 1000), 
        'question': '¿Cuáles son los gastos de marketing mensuales?'
    },
    {
        'answer': random.choice(['Semanalmente', 'Quincenalmente', 'Mensualmente', 'Bimensualmente']),
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
        'answer': random.randint(10, 100),
        'question': '¿Cuántos artículos produce en cada lote de producción?'
    },
    {
        'answer': random.randint(1, 10),
        'question': '¿Cuánto tiempo tarda cada empleado en producir una unidad de producto?'
    },
    {
        'answer': random.randint(5, 10), 
        'question': '¿Cómo calificaría la calidad del producto final en una escala de 1 a 10?'
    },  
    {
        'answer': round(random.uniform(0.1, 1), 2), 
        'question': '¿Cuál es el costo por unidad de transportar el producto de la fábrica a la tienda?'
    }
]
    