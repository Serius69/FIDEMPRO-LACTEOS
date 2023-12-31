# Generated by Django 4.2.7 on 2023-11-21 08:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0001_initial'),
        ('simulate', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Demand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=0, help_text='The quantity of the demand')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the business is active or not', verbose_name='Active')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='The date the business was created', null=True, verbose_name='Date Created')),
                ('last_updated', models.DateTimeField(auto_now=True, help_text='The date the business was last updated', null=True, verbose_name='Last Updated')),
                ('is_predicted', models.BooleanField(default=False, help_text='Whether the demand is predicted or not', verbose_name='Predicted')),
                ('fk_product', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='fk_product_demand_behavior', to='product.product')),
                ('fk_result_simulation', models.ForeignKey(default=1, help_text='The result simulation associated with the demand', on_delete=django.db.models.deletion.CASCADE, related_name='fk_result_simulation_demand', to='simulate.resultsimulation', verbose_name='Result Simulation')),
            ],
        ),
        migrations.CreateModel(
            name='DemandBehavior',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the business is active or not', verbose_name='Active')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='The date the business was created', null=True, verbose_name='Date Created')),
                ('last_updated', models.DateTimeField(auto_now=True, help_text='The date the business was last updated', null=True, verbose_name='Last Updated')),
                ('current_demand', models.OneToOneField(blank=True, default=1, on_delete=django.db.models.deletion.CASCADE, related_name='fk_demand_behavior_current_demand', to='dashboards.demand')),
                ('predicted_demand', models.OneToOneField(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='fk_demand_behavior_predicted_demand', to='dashboards.demand')),
            ],
        ),
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='Dashboard', help_text='The title of the dashboard.', max_length=255)),
                ('chart_type', models.CharField(default='line', help_text='The type of chart to use for the dashboard.', max_length=50)),
                ('chart_data', models.JSONField(default=dict, help_text='Structured JSON data for chart configuration.')),
                ('widget_config', models.JSONField(default=dict, help_text='Structured JSON data for widget configuration.')),
                ('layout_config', models.JSONField(default=dict, help_text='Structured JSON data for layout configuration.')),
                ('is_active', models.BooleanField(default=True, help_text='Whether the dashboard is active or not', verbose_name='Active')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='The date the dashboard was created', null=True, verbose_name='Date Created')),
                ('last_updated', models.DateTimeField(auto_now=True, help_text='The date the dashboard was last updated', null=True, verbose_name='Last Updated')),
                ('fk_product', models.ForeignKey(default=1, help_text='The product associated with the dashboard.', on_delete=django.db.models.deletion.CASCADE, related_name='fk_product_dashboard', to='product.product')),
            ],
        ),
    ]
