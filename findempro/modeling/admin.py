from django.contrib import admin

from .models import BusinessDataImport, BusinessModelDefinition, BusinessModelTemplate, BusinessModelVersion, BusinessScenario, BusinessSimulationRun


@admin.register(BusinessModelDefinition)
class BusinessModelDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "sector", "reference_data_source", "status", "updated_at")
    list_filter = ("status", "sector", "reference_data_source")
    search_fields = ("name", "business__name")


@admin.register(BusinessModelVersion)
class BusinessModelVersionAdmin(admin.ModelAdmin):
    list_display = ("definition", "version", "status", "content_hash", "created_at")
    readonly_fields = ("content_hash", "created_at")
    list_filter = ("status", "schema_version")


@admin.register(BusinessModelTemplate)
class BusinessModelTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sector", "is_builtin", "is_active")
    list_filter = ("sector", "is_builtin", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BusinessScenario)
class BusinessScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "model_version", "label", "created_at")


@admin.register(BusinessSimulationRun)
class BusinessSimulationRunAdmin(admin.ModelAdmin):
    list_display = ("id", "model_version", "engine", "reference_data_source", "status", "progress", "created_at")
    list_filter = ("engine", "status", "reference_data_source")


@admin.register(BusinessDataImport)
class BusinessDataImportAdmin(admin.ModelAdmin):
    list_display = ("source_name", "model_version", "format", "status", "rows_imported", "created_at")
    list_filter = ("format", "status")
    readonly_fields = ("rows", "error_rows", "provenance", "created_at")
