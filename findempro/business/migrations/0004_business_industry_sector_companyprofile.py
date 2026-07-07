"""
Migration: 0004 — Generalización multi-industria
- Agrega campo industry_sector a Business
- Cambia default de type de DAIRY (1) a OTHER (7)
- Crea modelo CompanyProfile para configuración por empresa
"""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0003_remove_business_unique_business_name_per_user_and_more'),
    ]

    operations = [
        # 1. Agregar campo industry_sector a Business
        migrations.AddField(
            model_name='business',
            name='industry_sector',
            field=models.CharField(
                choices=[
                    ('production', 'Producción'),
                    ('retail', 'Comercio / Retail'),
                    ('services', 'Servicios'),
                    ('agro', 'Agropecuario'),
                    ('manufacturing', 'Manufactura'),
                    ('other', 'Otro'),
                ],
                default='other',
                help_text='Sector macro del negocio (calculado automáticamente)',
                max_length=20,
                verbose_name='Sector',
                db_index=True,
            ),
        ),

        # 2. Cambiar default del campo type de DAIRY (1) a OTHER (7)
        migrations.AlterField(
            model_name='business',
            name='type',
            field=models.IntegerField(
                choices=[
                    (1, 'Lácteos'),
                    (2, 'Agricultura'),
                    (3, 'Bienes de Consumo'),
                    (4, 'Panadería'),
                    (5, 'Carnicería'),
                    (6, 'Verdulería / Minimarket'),
                    (7, 'Otros'),
                    (8, 'Manufactura Alimentaria'),
                    (9, 'Manufactura General'),
                    (10, 'Retail / Comercio'),
                    (11, 'Mayorista'),
                    (12, 'Servicios Generales'),
                    (13, 'Salud'),
                    (14, 'Educación'),
                    (15, 'Logística / Transporte'),
                    (16, 'Hotelería / Restaurantes'),
                    (17, 'Tecnología / Software'),
                    (18, 'Construcción'),
                    (19, 'Servicios Financieros'),
                ],
                default=7,
                help_text='El tipo/industria del negocio',
                verbose_name='Tipo de Industria',
            ),
        ),

        # 3. Crear modelo CompanyProfile
        migrations.CreateModel(
            name='CompanyProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_cost_driver', models.CharField(
                    default='costo_produccion',
                    help_text='Nombre de la variable que más impacta los costos',
                    max_length=100,
                    verbose_name='Variable de Costo Principal',
                )),
                ('primary_revenue_driver', models.CharField(
                    default='precio_venta',
                    help_text='Variable que determina los ingresos',
                    max_length=100,
                    verbose_name='Variable de Ingreso Principal',
                )),
                ('demand_variable_name', models.CharField(
                    default='demanda',
                    help_text='Nombre de la variable de demanda en las ecuaciones',
                    max_length=100,
                    verbose_name='Nombre Variable de Demanda',
                )),
                ('demand_pattern', models.CharField(
                    choices=[
                        ('stable', 'Estable'),
                        ('seasonal', 'Estacional'),
                        ('trending_up', 'Creciente'),
                        ('trending_down', 'Decreciente'),
                        ('volatile', 'Volátil'),
                        ('cyclic', 'Cíclico'),
                    ],
                    default='stable',
                    max_length=20,
                    verbose_name='Patrón de Demanda',
                )),
                ('seasonality_factor', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Lista de 12 factores mensuales [ene..dic]',
                    verbose_name='Factores de Estacionalidad',
                )),
                ('peak_months', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Lista de meses con alta demanda [1=enero..12=diciembre]',
                    verbose_name='Meses Pico',
                )),
                ('distribution_preference', models.CharField(
                    choices=[
                        ('auto', 'Automática (mejor ajuste)'),
                        ('normal', 'Normal'),
                        ('lognormal', 'Log-Normal'),
                        ('gamma', 'Gamma'),
                        ('uniform', 'Uniforme'),
                    ],
                    default='auto',
                    max_length=20,
                    verbose_name='Distribución Estadística',
                )),
                ('monte_carlo_iterations', models.PositiveIntegerField(
                    default=10000,
                    help_text='Número de iteraciones para la simulación (1000-100000)',
                    verbose_name='Iteraciones Monte Carlo',
                )),
                ('confidence_level', models.FloatField(
                    default=0.95,
                    help_text='Nivel de confianza estadístico (0.80-0.99)',
                    verbose_name='Nivel de Confianza',
                )),
                ('min_profit_margin_pct', models.FloatField(
                    default=10.0,
                    help_text='Umbral mínimo aceptable de margen de ganancia',
                    verbose_name='Margen de Ganancia Mínimo (%)',
                )),
                ('max_cost_revenue_ratio', models.FloatField(
                    default=70.0,
                    help_text='Alerta si los costos superan este % de los ingresos',
                    verbose_name='Ratio Costo/Ingreso Máximo (%)',
                )),
                ('inventory_days_target', models.PositiveIntegerField(
                    default=30,
                    help_text='Días ideales de stock de seguridad',
                    verbose_name='Días de Inventario Objetivo',
                )),
                ('custom_kpis', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Diccionario de KPIs específicos de la industria',
                    verbose_name='KPIs Personalizados',
                )),
                ('simulation_notes', models.TextField(
                    blank=True,
                    default='',
                    verbose_name='Notas de Configuración',
                )),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('fk_business', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='company_profile',
                    to='business.business',
                    verbose_name='Negocio',
                )),
            ],
            options={
                'verbose_name': 'Perfil de Empresa',
                'verbose_name_plural': 'Perfiles de Empresa',
            },
        ),
    ]
