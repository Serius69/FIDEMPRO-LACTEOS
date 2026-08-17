from django.urls import path

from . import views

app_name = "modeling"

urlpatterns = [
    path("businesses/", views.business_list, name="business-list"),
    path("templates/", views.template_list, name="template-list"),
    path("models/", views.model_list_create, name="model-list-create"),
    path("models/<uuid:model_id>/export/", views.model_export, name="model-export"),
    path("models/<uuid:model_id>/", views.model_detail, name="model-detail"),
    path("models/<uuid:model_id>/validate/", views.model_validate, name="model-validate"),
    path("models/<uuid:model_id>/diagrams/", views.model_diagrams, name="model-diagrams"),
    path("models/<uuid:model_id>/versions/", views.model_version_create, name="model-version-create"),
    path("models/<uuid:model_id>/scenarios/", views.scenario_list_create, name="scenario-list-create"),
    path("models/<uuid:model_id>/imports/", views.data_import_create, name="data-import-create"),
    path("models/<uuid:model_id>/simulate/", views.model_simulate, name="model-simulate"),
    path("models/<uuid:model_id>/sensitivity/", views.model_sensitivity, name="model-sensitivity"),
    path("models/<uuid:model_id>/distribution-fit/", views.model_distribution_fit, name="model-distribution-fit"),
    path("runs/", views.run_list, name="run-list"),
    path("runs/compare/", views.run_compare, name="run-compare"),
    path("runs/<uuid:run_id>/cancel/", views.run_cancel, name="run-cancel"),
    path("runs/<uuid:run_id>/report/", views.run_report, name="run-report"),
    path("runs/<uuid:run_id>/", views.run_detail, name="run-detail"),
]
