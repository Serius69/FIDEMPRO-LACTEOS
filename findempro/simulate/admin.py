from django.contrib import admin

from .models import (
    ProbabilisticDensityFunction,
    Simulation,
    ResultSimulation,
    RiskAlert,
)
from .canvas_models import SimulationProject, ModelNode, ModelEdge


@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'var_threshold', 'cvar_threshold', 'email', 'is_active', 'created_at']
    list_filter  = ['is_active', 'created_at']
    search_fields = ['user__username', 'email', 'fk_product__name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields  = ['user', 'fk_product']


@admin.register(SimulationProject)
class SimulationProjectAdmin(admin.ModelAdmin):
    list_display  = ['id', 'name', 'domain', 'user', 'created_at', 'updated_at']
    list_filter   = ['domain', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display  = ['id', 'unit_time', 'quantity_time', 'is_completed', 'is_active', 'date_created']
    list_filter   = ['is_completed', 'is_active', 'unit_time']
    readonly_fields = ['date_created', 'last_updated']
