# Generated by Django 3.2 on 2023-01-05 05:59

from django.db import migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0004_auto_20230105_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crmcontact',
            name='tags',
            field=multiselectfield.db.fields.MultiSelectField(choices=[(1, 'Lead'), (2, 'Partner'), (3, 'Exiting'), (4, 'Long-term')], max_length=50),
        ),
        migrations.AlterField(
            model_name='crmlead',
            name='tags',
            field=multiselectfield.db.fields.MultiSelectField(choices=[(1, 'Lead'), (2, 'Partner'), (3, 'Exiting'), (4, 'Long-term')], max_length=50),
        ),
    ]