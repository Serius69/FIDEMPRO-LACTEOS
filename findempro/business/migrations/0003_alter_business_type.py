# Generated by Django 4.2.5 on 2023-11-19 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0002_alter_business_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='business',
            name='type',
            field=models.IntegerField(default=1, help_text='The type of the business', verbose_name='Type'),
        ),
    ]