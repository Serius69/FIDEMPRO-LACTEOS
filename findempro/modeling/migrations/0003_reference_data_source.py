from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("modeling", "0002_businessdataimport")]

    operations = [
        migrations.AddField(
            model_name="businessmodeldefinition",
            name="reference_data_source",
            field=models.CharField(
                choices=[
                    ("CUSTOMER_PRIVATE", "Datos privados del cliente"),
                    ("KDP_GOVERNED", "Referencias compartidas gobernadas por KDP"),
                ],
                default="CUSTOMER_PRIVATE",
                help_text=(
                    "Selecciona la autoridad para datos de referencia compartidos. "
                    "Los modelos, imports y resultados privados siempre permanecen en Findempro."
                ),
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="businesssimulationrun",
            name="reference_data_source",
            field=models.CharField(
                choices=[
                    ("CUSTOMER_PRIVATE", "Datos privados del cliente"),
                    ("KDP_GOVERNED", "Referencias compartidas gobernadas por KDP"),
                ],
                default="CUSTOMER_PRIVATE",
                editable=False,
                max_length=20,
            ),
        ),
    ]
