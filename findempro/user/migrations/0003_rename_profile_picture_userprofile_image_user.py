# Generated by Django 4.2.5 on 2023-11-18 19:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_userprofile_country_userprofile_state'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='profile_picture',
            new_name='image_user',
        ),
    ]