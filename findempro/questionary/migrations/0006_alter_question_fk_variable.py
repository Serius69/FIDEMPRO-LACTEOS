# Generated by Django 4.2.5 on 2023-11-15 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('variable', '0007_alter_variable_image_src'),
        ('questionary', '0005_question_fk_variable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='fk_variable',
            field=models.ForeignKey(default=1, help_text='The variable associated with the question', on_delete=django.db.models.deletion.CASCADE, related_name='fk_variable_question', to='variable.variable'),
        ),
    ]