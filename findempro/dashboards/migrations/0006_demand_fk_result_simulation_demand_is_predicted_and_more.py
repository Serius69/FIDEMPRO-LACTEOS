# Generated by Django 4.2.5 on 2023-11-18 23:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_area'),
        ('simulate', '0002_alter_fdp_distribution_type_and_more'),
        ('dashboards', '0005_remove_demandbehavior_fk_demand_dashboard_chart_data_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='demand',
            name='fk_result_simulation',
            field=models.ForeignKey(default=1, help_text='The result simulation associated with the demand', on_delete=django.db.models.deletion.CASCADE, related_name='fk_result_simulation_demand', to='simulate.resultsimulation', verbose_name='Result Simulation'),
        ),
        migrations.AddField(
            model_name='demand',
            name='is_predicted',
            field=models.BooleanField(default=False, help_text='Whether the demand is predicted or not', verbose_name='Predicted'),
        ),
        migrations.AlterField(
            model_name='demand',
            name='fk_product',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='fk_product_demand_behavior', to='product.product'),
        ),
        migrations.AlterField(
            model_name='demand',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='demandbehavior',
            name='current_demand',
            field=models.OneToOneField(blank=True, default=1, on_delete=django.db.models.deletion.CASCADE, related_name='fk_demand_behavior_current_demand', to='dashboards.demand'),
        ),
        migrations.AlterField(
            model_name='demandbehavior',
            name='predicted_demand',
            field=models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_demand_behavior_predicted_demand', to='dashboards.demand'),
        ),
    ]