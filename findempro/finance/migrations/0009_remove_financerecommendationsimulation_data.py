from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0008_financerecommendationsimulation_data_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="financerecommendationsimulation",
            name="data",
        ),
    ]
