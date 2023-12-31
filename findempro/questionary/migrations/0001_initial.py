# Generated by Django 4.2.7 on 2023-11-21 08:38

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('variable', '0001_initial'),
        ('business', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Questionary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('questionary', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('fk_business', models.ForeignKey(default=1, help_text='The business associated with the questionnaire', on_delete=django.db.models.deletion.CASCADE, related_name='fk_business_questionary', to='business.business')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionaryResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now, help_text='The date the question was created')),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now, help_text='The date the question was last updated')),
                ('fk_questionary', models.ForeignKey(default=1, help_text='The questionnaire associated with the question', on_delete=django.db.models.deletion.CASCADE, related_name='fk_questionary_questionary_result', to='questionary.questionary')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.TextField()),
                ('type', models.IntegerField(default=1, help_text='The type of question')),
                ('is_active', models.BooleanField(default=True, help_text='The status of the question')),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now, help_text='The date the question was created')),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now, help_text='The date the question was last updated')),
                ('fk_questionary', models.ForeignKey(help_text='The questionnaire associated with the question', on_delete=django.db.models.deletion.CASCADE, related_name='fk_questionary_question', to='questionary.questionary')),
                ('fk_variable', models.ForeignKey(help_text='The variable associated with the question', on_delete=django.db.models.deletion.CASCADE, related_name='fk_variable_question', to='variable.variable')),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('fk_question', models.ForeignKey(help_text='The question associated with the answer', on_delete=django.db.models.deletion.CASCADE, related_name='fk_question_answer', to='questionary.question')),
                ('fk_questionary_result', models.ForeignKey(default=1, help_text='The questionary result associated with the answer', on_delete=django.db.models.deletion.CASCADE, related_name='fk_question_result_answer', to='questionary.questionaryresult')),
            ],
        ),
    ]
