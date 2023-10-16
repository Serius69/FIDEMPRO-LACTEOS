import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tu_proyecto.settings")  # Reemplaza 'tu_proyecto' con el nombre de tu proyecto.
django.setup()


from variable.models import Variable  # Reemplaza 'your_app' con el nombre de tu aplicación.

variables_data = [
    {
        'name': 'NÚMERO MÁXIMO UNIDAD DE TIEMPO',
        'initials': 'NMD',
        'type': 'EXÓGENA',
        'unit': 'UNIDAD DE TIEMPO',
        'description': 'CANTIDAD DE UNIDAD DE TIEMPO',
    },
    # Agrega los otros 49 registros de manera similar
]


for data in variables_data:
    Variable.objects.create(**data)

# python generate_records.py