import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('simulate', '0018_v2_canvas'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SimulationShareToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)),
                ('simulation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='share_tokens',
                    to='simulate.simulation',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='simulation_share_tokens',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('expires_at', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('access_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Token de compartición',
                'verbose_name_plural': 'Tokens de compartición',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['token', 'is_active'], name='share_token_lookup'),
                ],
            },
        ),
    ]
