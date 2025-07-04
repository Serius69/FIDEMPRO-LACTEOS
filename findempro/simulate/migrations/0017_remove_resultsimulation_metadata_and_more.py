# Generated by Django 4.2.11 on 2025-06-25 04:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulate", "0016_resultsimulation_metadata"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="resultsimulation",
            name="metadata",
        ),
        migrations.RemoveField(
            model_name="simulation",
            name="completion_date",
        ),
        migrations.RemoveField(
            model_name="simulation",
            name="demand_config",
        ),
        migrations.RemoveField(
            model_name="simulation",
            name="execution_report",
        ),
        migrations.RemoveField(
            model_name="simulation",
            name="extracted_variables",
        ),
        migrations.RemoveField(
            model_name="simulation",
            name="extraction_report",
        ),
        migrations.AlterField(
            model_name="simulation",
            name="is_completed",
            field=models.BooleanField(
                default=False, help_text="Whether the simulation has been completed"
            ),
        ),
    ]
