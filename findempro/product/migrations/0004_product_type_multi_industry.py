"""
Migration: 0004 — Generalizar tipo de producto multi-industria
Reemplaza TYPE_CHOICES hardcodeados de Lácteos/Servicio
por categorías genéricas aplicables a cualquier PyME.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_alter_area_options_alter_product_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='type',
            field=models.IntegerField(
                choices=[
                    (1, 'Producto Físico'),
                    (2, 'Servicio'),
                    (3, 'Materia Prima'),
                    (4, 'Producto Semi-elaborado'),
                    (5, 'Producto Terminado'),
                    (6, 'Activo / Recurso'),
                    (7, 'Digital / Software'),
                    (8, 'Agropecuario'),
                    (9, 'Otro'),
                ],
                default=1,
                verbose_name='Categoría de Producto/Servicio',
            ),
        ),
    ]
