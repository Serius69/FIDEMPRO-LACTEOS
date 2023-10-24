import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "findempro.settings")  # Reemplaza 'tu_proyecto' con el nombre de tu proyecto.
django.setup()

from product.models import Product  # Reemplaza 'your_app' con el nombre de tu aplicación.


products_data = [
    
    {'name': 'Milk',
    'description': 'La leche es un alimento básico completo y equilibrado, proporcionando un elevado contenido de nutrientes (Proteínas, Hidratos de Carbono, Vitaminas, Minerales y Lípidos) en relación al contenido calórico. 2. Su valor como bebida nutritiva es incomparable al resto de las bebidas existentes en el mercado.',
    'image_src': 'images/product/soles.jpg',
    'fk_business': 1,
    'type': 'Dairy',
    },
    {'name': 'Cheese',
    'description': 'El queso es un alimento elaborado a partir de la leche cuajada de vaca, cabra, oveja u otros mamíferos. Sus diferentes estilos y sabores son el resultado del uso de distintas especies de bacterias y mohos, niveles de nata en la leche, curación, tratamientos en su proceso, etc.',
    'image_src': 'images/product/soles.jpg',
    'fk_business': 1,
    'type': 'Dairy',
    },
    {'name': 'Yogurt',
    'description': 'El yogur es uno de los alimentos que se ha normalizado como postre diario en muchas sociedades. Además de su valor nutritivo, ¡está muy rico! Un yogur natural es un producto lácteo obtenido por la fermentación de microorganismos específicos de la leche.',
    'image_src': 'images/product/soles.jpg',
    'fk_business': 1,
    'type': 'Dairy',
    },
    ]



for data in products_data:
    Product.objects.create(**data)
    
    # python generate_products.py