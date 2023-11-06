import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "findempro.settings")  # Reemplaza 'tu_proyecto' con el nombre de tu proyecto.
django.setup()

from questionary.models import Questionary,Question   # Reemplaza 'your_app' con el nombre de tu aplicación.


questionary_data = [
    {'questionary': 'Milk Questionary',
    'fk_test': 1,
    'type': 1,
    },
        ]

question_data = [
    {
        'question': '¿Cuántos productos lácteos vende diariamente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el precio actual de sus productos lácteos?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': 'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuántos productos están siendo producidos actualmente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es la demanda esperada para los productos lácteos?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el costo unitario de producción?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es la capacidad del inventario de productos?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Existe estacionalidad en la demanda?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el costo unitario del insumo para la producción?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de competitividad en el mercado de su empresa?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cómo se posiciona su empresa en el mercado?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Con qué frecuencia compran los clientes?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es la tasa de retención de clientes de su empresa?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de satisfacción del cliente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de lealtad del cliente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuánto cuesta adquirir un nuevo cliente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuánto cuesta adquirir un nuevo cliente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuánto cuesta retener a un cliente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuántos clientes llegan diariamente?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de automatización del proceso de producción?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de eficiencia del proceso de producción?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿La empresa cuenta con certificaciones de calidad?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuánto tiempo tarda en producir un producto?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de capacidad de producción?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de flexibilidad en la producción?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de eficiencia del inventario?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de eficiencia en la cadena de suministro?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de eficiencia en la gestión de compra de insumos?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el nivel de eficiencia en la gestión de ventas?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuáles son los sueldos y salarios de los empleados?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el precio actual de los productos lácteos de la competencia?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el costo fijo diario?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el costo unitario por transporte?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es el costo unitario del inventario?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuáles son los gastos de marketing mensuales?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cada cuánto tiempo se reabastece de insumos?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuántos insumos se utilizan para fabricar un producto lácteo?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
    {
        'question': '¿Cuál es la capacidad máxima de almacenamiento en inventario de productos lácteos?',
        'fk_questionary': 1,  # Replace with the appropriate foreign key value
        'type': 1,
    },
]

for data in questionary_data:
    Questionary.objects.create(**data)


for data in question_data:
    Question.objects.create(**data)
    
    # python generate_questions.py