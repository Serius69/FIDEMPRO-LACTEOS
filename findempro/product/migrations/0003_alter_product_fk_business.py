# Generated by Django 4.2.5 on 2023-11-12 04:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0004_business_fk_user'),
        ('product', '0002_alter_product_last_updated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='fk_business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='fk_business_product', to='business.business'),
        ),
    ]