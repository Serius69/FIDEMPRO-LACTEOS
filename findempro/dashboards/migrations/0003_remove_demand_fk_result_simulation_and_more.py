# Generated by Django 4.2.7 on 2023-11-29 21:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('simulate', '0009_delete_demandhistorical'),
        ('dashboards', '0002_chart_delete_dashboard'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='demand',
            name='fk_result_simulation',
        ),
        migrations.AddField(
            model_name='demand',
            name='fk_simulation',
            field=models.ForeignKey(default=1, help_text='The result simulation associated with the demand', on_delete=django.db.models.deletion.CASCADE, related_name='fk_result_simulation_demand', to='simulate.simulation', verbose_name='Result Simulation'),
        ),
    ]