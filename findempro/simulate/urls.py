from django.urls import path
from .views.simulate_init_view import AppsView, simulate_show_view
from .views.simulate_result_view import simulate_result_simulation_view
from .views.simulate_list_view import SimulateListView, simulate_add_view

from .views.api_views import (
    SimulationProgressView,
    SimulationRetryView,
    SimulationDuplicateView,
    SimulationStartView,
    SimulationDeleteView,
    SimulationCompareView,
    SimulationSensitivityView,
    SimulationHistoryView,
    SimulationExportView,
    SimulationShareCreateView,
    SimulationShareAccessView,
)
from .views.api_v1_views import (
    SimulateAPIView,
    ForecastAPIView,
    RiskAnalysisAPIView,
    ScenariosAPIView,
    CompanyProfileAPIView,
    FullPipelineAPIView,
)

app_name = 'simulate'

urlpatterns = [
    # ── Vistas principales de simulación ────────────────────────────────────────
    path("", view=AppsView.as_view(), name="simulate.index"),
    path("init/", view=simulate_show_view, name="simulate.show"),
    path("add/", view=simulate_add_view, name="simulate.add"),
    path("result/<int:simulation_id>/", view=simulate_result_simulation_view, name="simulate.result"),
    path("result/<int:simulation_id>/edit/", view=simulate_add_view, name="simulate.edit"),
    path("result/<int:simulation_id>/delete/", view=simulate_add_view, name="simulate.delete"),
    path("result/<int:simulation_id>/view/", view=simulate_result_simulation_view, name="simulate.view"),
    path("list/", view=SimulateListView.as_view(), name="simulate.list"),

    # ── API legacy (endpoints existentes) ───────────────────────────────────────
    path("api/progress/<int:simulation_id>/", view=SimulationProgressView.as_view(), name="api.progress"),
    path("api/retry/<int:simulation_id>/", view=SimulationRetryView.as_view(), name="api.retry"),
    path("api/duplicate/<int:simulation_id>/", view=SimulationDuplicateView.as_view(), name="api.duplicate"),
    path("api/start/<int:simulation_id>/", view=SimulationStartView.as_view(), name="api.start"),
    path("api/delete/<int:simulation_id>/", view=SimulationDeleteView.as_view(), name="api.delete"),

    # ── FASE 4 — New analytics endpoints ────────────────────────────────────────
    path("api/compare/", view=SimulationCompareView.as_view(), name="api.compare"),
    path("api/sensitivity/<int:simulation_id>/", view=SimulationSensitivityView.as_view(), name="api.sensitivity"),
    path("api/history/", view=SimulationHistoryView.as_view(), name="api.history"),
    path("api/export/<int:simulation_id>/", view=SimulationExportView.as_view(), name="api.export"),

    # ── Compartir por enlace temporal (público, sin auth) ───────────────────────
    path("api/share/<int:simulation_id>/", view=SimulationShareCreateView.as_view(), name="api.share.create"),
    path("share/<uuid:token>/",            view=SimulationShareAccessView.as_view(), name="share.access"),

    # ── API v1 — Motor genérico multi-industria ─────────────────────────────────
    # Simulación Monte Carlo completa
    path("api/v1/simulate/", view=SimulateAPIView.as_view(), name="api.v1.simulate"),
    # Proyección de demanda a partir de histórico
    path("api/v1/forecast/", view=ForecastAPIView.as_view(), name="api.v1.forecast"),
    # Análisis de riesgo financiero
    path("api/v1/risk-analysis/", view=RiskAnalysisAPIView.as_view(), name="api.v1.risk_analysis"),
    # Escenarios financieros (pesimista/base/optimista)
    path("api/v1/scenarios/", view=ScenariosAPIView.as_view(), name="api.v1.scenarios"),
    # Perfil de configuración por empresa
    path("api/v1/company-profile/<int:business_id>/", view=CompanyProfileAPIView.as_view(), name="api.v1.company_profile"),
    # Pipeline completo: Monte Carlo + Eventos Discretos + Motor de Decisión
    path("api/v1/full-pipeline/<int:simulation_id>/", view=FullPipelineAPIView.as_view(), name="api.v1.full_pipeline"),
]