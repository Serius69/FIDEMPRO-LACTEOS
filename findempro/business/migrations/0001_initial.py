# Generated by Django 4.2.5 on 2023-11-19 16:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the business', max_length=255, verbose_name='Name')),
                ('type', models.IntegerField(default=1, help_text='The type of the business', verbose_name='Type')),
                ('location', models.CharField(help_text='The location of the business', max_length=255, verbose_name='Location')),
                ('image_src', models.ImageField(blank=True, help_text='The image of the business', null=True, upload_to='images/business', verbose_name='Image')),
                ('description', models.TextField(help_text='The description of the business', verbose_name='Description')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the business is active or not', verbose_name='Active')),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now, help_text='The date the business was created', verbose_name='Date Created')),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('fk_user', models.ForeignKey(default=1, help_text='The user associated with the business', on_delete=django.db.models.deletion.CASCADE, related_name='fk_user_business', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]