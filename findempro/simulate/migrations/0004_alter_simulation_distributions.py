# Generated by Django 4.2.7 on 2023-11-21 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulate', '0003_historicaldemand_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simulation',
            name='distributions',
            field=models.ManyToManyField(help_text='The ProbabilisticDensityFunctions associated with the simulation', related_name='simulations', to='simulate.probabilisticdensityfunction'),
        ),
    ]