# Generated by Django 4.2.7 on 2023-11-30 03:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0003_remove_demand_fk_result_simulation_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='demandbehavior',
            name='current_demand',
        ),
        migrations.RemoveField(
            model_name='demandbehavior',
            name='predicted_demand',
        ),
        migrations.DeleteModel(
            name='Demand',
        ),
        migrations.DeleteModel(
            name='DemandBehavior',
        ),
    ]
