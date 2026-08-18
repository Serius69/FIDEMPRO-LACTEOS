from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('business', '0005_alter_business_type_alter_companyprofile_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessModelDefinition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=180)),
                ('description', models.TextField(blank=True)),
                ('sector', models.CharField(db_index=True, default='generic', max_length=80)),
                ('status', models.CharField(choices=[('draft', 'Borrador'), ('validated', 'Validado'), ('published', 'Publicado'), ('archived', 'Archivado')], default='draft', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='model_definitions', to='business.business')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_model_definitions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='BusinessModelVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('version', models.PositiveIntegerField()),
                ('schema_version', models.CharField(default='1.0', max_length=20)),
                ('status', models.CharField(choices=[('draft', 'Borrador'), ('validated', 'Validado'), ('published', 'Publicado'), ('superseded', 'Reemplazado')], default='draft', max_length=20)),
                ('spec', models.JSONField(default=dict)),
                ('content_hash', models.CharField(editable=False, max_length=64)),
                ('validation', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_model_versions', to=settings.AUTH_USER_MODEL)),
                ('definition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='modeling.businessmodeldefinition')),
                ('parent_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='modeling.businessmodelversion')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BusinessScenario',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=160)),
                ('label', models.CharField(default='custom', max_length=30)),
                ('changes', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_business_scenarios', to=settings.AUTH_USER_MODEL)),
                ('model_version', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='scenarios', to='modeling.businessmodelversion')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BusinessModelTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=180)),
                ('sector', models.CharField(db_index=True, default='generic', max_length=80)),
                ('description', models.TextField(blank=True)),
                ('spec', models.JSONField(default=dict)),
                ('provenance', models.JSONField(blank=True, default=dict)),
                ('is_builtin', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_model_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='businessmodeldefinition',
            name='current_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='current_for_definitions', to='modeling.businessmodelversion'),
        ),
        migrations.CreateModel(
            name='BusinessSimulationRun',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('engine', models.CharField(default='monte_carlo', max_length=40)),
                ('status', models.CharField(choices=[('queued', 'Encolada'), ('running', 'En ejecución'), ('completed', 'Completada'), ('failed', 'Fallida'), ('cancelled', 'Cancelada')], default='queued', max_length=20)),
                ('seed', models.BigIntegerField(blank=True, null=True)),
                ('parameters_snapshot', models.JSONField(blank=True, default=dict)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('error', models.TextField(blank=True)),
                ('progress', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='business_simulation_runs', to=settings.AUTH_USER_MODEL)),
                ('model_version', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='simulation_runs', to='modeling.businessmodelversion')),
                ('scenario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='runs', to='modeling.businessscenario')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['model_version', 'status'], name='modeling_bu_model_v_fcc213_idx'), models.Index(fields=['created_by', 'created_at'], name='modeling_bu_created_105f2b_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='businessscenario',
            constraint=models.UniqueConstraint(fields=('model_version', 'name'), name='uniq_scenario_per_model_version'),
        ),
        migrations.AddIndex(
            model_name='businessmodelversion',
            index=models.Index(fields=['definition', 'status'], name='modeling_bu_definit_f74770_idx'),
        ),
        migrations.AddIndex(
            model_name='businessmodelversion',
            index=models.Index(fields=['content_hash'], name='modeling_bu_content_134cae_idx'),
        ),
        migrations.AddConstraint(
            model_name='businessmodelversion',
            constraint=models.UniqueConstraint(fields=('definition', 'version'), name='uniq_model_definition_version'),
        ),
        migrations.AddIndex(
            model_name='businessmodeldefinition',
            index=models.Index(fields=['business', 'status'], name='modeling_bu_busines_90ab40_idx'),
        ),
        migrations.AddIndex(
            model_name='businessmodeldefinition',
            index=models.Index(fields=['sector', 'status'], name='modeling_bu_sector_d70030_idx'),
        ),
    ]
