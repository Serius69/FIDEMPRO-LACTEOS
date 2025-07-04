# Generated by Django 4.2.11 on 2025-07-03 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0007_alter_financerecommendationsimulation_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="financerecommendationsimulation",
            name="data",
            field=models.FloatField(
                blank=True,
                help_text="Campo de datos numéricos (deprecado, usar metric_value)",
                null=True,
                verbose_name="Datos",
            ),
        ),
        migrations.AddField(
            model_name="financerecommendationsimulation",
            name="date_updated",
            field=models.DateTimeField(
                auto_now=True, verbose_name="Fecha de Actualización"
            ),
        ),
        migrations.AddField(
            model_name="financerecommendationsimulation",
            name="priority",
            field=models.CharField(
                choices=[("low", "Baja"), ("medium", "Media"), ("high", "Alta")],
                default="medium",
                help_text="Prioridad de la recomendación",
                max_length=20,
                verbose_name="Prioridad",
            ),
        ),
        migrations.AddField(
            model_name="financerecommendationsimulation",
            name="recommendation",
            field=models.TextField(
                blank=True,
                help_text="Texto de la recomendación específica",
                null=True,
                verbose_name="Recomendación",
            ),
        ),
        migrations.AddField(
            model_name="financerecommendationsimulation",
            name="threshold",
            field=models.FloatField(
                blank=True,
                help_text="Valor umbral para la recomendación",
                null=True,
                verbose_name="Umbral",
            ),
        ),
        migrations.AddField(
            model_name="financerecommendationsimulation",
            name="value",
            field=models.FloatField(
                blank=True,
                help_text="Valor actual de la métrica",
                null=True,
                verbose_name="Valor",
            ),
        ),
        migrations.AddField(
            model_name="financerecommendationsimulation",
            name="variable",
            field=models.CharField(
                blank=True,
                help_text="Variable asociada a la recomendación",
                max_length=50,
                null=True,
                verbose_name="Variable",
            ),
        ),
        migrations.AlterField(
            model_name="financerecommendationsimulation",
            name="category",
            field=models.CharField(
                choices=[
                    ("critical", "Crítico"),
                    ("profitability", "Rentabilidad"),
                    ("costs", "Costos"),
                    ("efficiency", "Eficiencia"),
                    ("trends", "Tendencias"),
                    ("financial", "Financiero"),
                ],
                default="financial",
                help_text="Categoría de la recomendación",
                max_length=50,
                verbose_name="Categoría",
            ),
        ),
        migrations.AddIndex(
            model_name="financerecommendationsimulation",
            index=models.Index(
                fields=["fk_simulation", "category"],
                name="finance_fin_fk_simu_10d740_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="financerecommendationsimulation",
            index=models.Index(
                fields=["severity", "priority"], name="finance_fin_severit_380462_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="financerecommendationsimulation",
            index=models.Index(
                fields=["date_created"], name="finance_fin_date_cr_4653b1_idx"
            ),
        ),
    ]
