# Generated by Django 4.2.5 on 2023-11-14 21:11

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_alter_product_fk_business'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_checked_for_simulation', models.BooleanField(default=False)),
                ('params', models.JSONField(blank=True, null=True)),
                ('fk_product', models.ForeignKey(default=1, help_text='The product associated with the area', on_delete=django.db.models.deletion.CASCADE, related_name='fk_product_area', to='product.product')),
            ],
        ),
    ]