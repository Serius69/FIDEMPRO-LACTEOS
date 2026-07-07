"""
URLs para la API v2 del canvas visual de FindemproAI.
Montadas en /api/v2/ desde findempro/urls.py.

Estructura:
  /api/v2/projects/                                       → ProjectViewSet
  /api/v2/projects/{pid}/nodes/                           → NodeViewSet
  /api/v2/projects/{pid}/nodes/batch-position/            → NodeViewSet.batch_position
  /api/v2/projects/{pid}/edges/                           → EdgeViewSet
  /api/v2/projects/{pid}/simulate/                        → SimulationRunView
  /api/v2/projects/{pid}/simulate/live-update/            → SimulationLiveUpdateView
  /api/v2/projects/{pid}/simulate/validate/               → SimulationValidateView
  /api/v2/projects/{pid}/simulate/sensitivity/            → SensitivityAnalysisView
  /api/v2/projects/{pid}/simulate/causal-diagram/         → CausalDiagramView
  /api/v2/projects/{pid}/runs/                            → SimulationRunListView
  /api/v2/projects/{pid}/runs/{rid}/                      → SimulationRunListView
  /api/v2/projects/{pid}/pages/                           → PageViewSet
  /api/v2/projects/{pid}/pages/{ppid}/widgets/            → WidgetViewSet
  /api/v2/projects/import/                                → ProjectViewSet.import_project
  /api/v2/alerts/                                         → RiskAlertViewSet
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.canvas_views import (
    CausalDiagramView,
    EdgeViewSet,
    NodeViewSet,
    PageViewSet,
    ProjectViewSet,
    RiskAlertViewSet,
    SensitivityAnalysisView,
    SimulationLiveUpdateView,
    SimulationRunListView,
    SimulationRunView,
    SimulationValidateView,
    WidgetViewSet,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="canvas-project")
router.register(r"alerts", RiskAlertViewSet, basename="risk-alert")

urlpatterns = [
    # ── Proyectos (router maneja list/create/retrieve/update/destroy) ──────────
    path("", include(router.urls)),

    # ── Nodos ────────────────────────────────────────────────────────────────────
    path(
        "projects/<uuid:project_pk>/nodes/",
        NodeViewSet.as_view({"get": "list", "post": "create"}),
        name="canvas-node-list",
    ),
    path(
        "projects/<uuid:project_pk>/nodes/batch-position/",
        NodeViewSet.as_view({"put": "batch_position"}),
        name="canvas-node-batch-position",
    ),
    path(
        "projects/<uuid:project_pk>/nodes/<uuid:pk>/",
        NodeViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="canvas-node-detail",
    ),

    # ── Edges ────────────────────────────────────────────────────────────────────
    path(
        "projects/<uuid:project_pk>/edges/",
        EdgeViewSet.as_view({"get": "list", "post": "create"}),
        name="canvas-edge-list",
    ),
    path(
        "projects/<uuid:project_pk>/edges/<uuid:pk>/",
        EdgeViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="canvas-edge-detail",
    ),

    # ── Simulación ───────────────────────────────────────────────────────────────
    path(
        "projects/<uuid:project_pk>/simulate/",
        SimulationRunView.as_view(),
        name="canvas-simulate",
    ),
    path(
        "projects/<uuid:project_pk>/simulate/live-update/",
        SimulationLiveUpdateView.as_view(),
        name="canvas-simulate-live",
    ),
    path(
        "projects/<uuid:project_pk>/simulate/validate/",
        SimulationValidateView.as_view(),
        name="canvas-simulate-validate",
    ),
    path(
        "projects/<uuid:project_pk>/simulate/causal-diagram/",
        CausalDiagramView.as_view(),
        name="canvas-causal-diagram",
    ),
    path(
        "projects/<uuid:project_pk>/simulate/sensitivity/",
        SensitivityAnalysisView.as_view(),
        name="canvas-sensitivity",
    ),

    # ── Historial de corridas ────────────────────────────────────────────────────
    path(
        "projects/<uuid:project_pk>/runs/",
        SimulationRunListView.as_view(),
        name="canvas-run-list",
    ),
    path(
        "projects/<uuid:project_pk>/runs/<uuid:run_pk>/",
        SimulationRunListView.as_view(),
        name="canvas-run-detail",
    ),

    # ── Interface Window: páginas ─────────────────────────────────────────────────
    path(
        "projects/<uuid:project_pk>/pages/",
        PageViewSet.as_view({"get": "list", "post": "create"}),
        name="canvas-page-list",
    ),
    path(
        "projects/<uuid:project_pk>/pages/<uuid:pk>/",
        PageViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="canvas-page-detail",
    ),

    # ── Interface Window: widgets ─────────────────────────────────────────────────
    path(
        "projects/<uuid:project_pk>/pages/<uuid:page_pk>/widgets/",
        WidgetViewSet.as_view({"get": "list", "post": "create"}),
        name="canvas-widget-list",
    ),
    path(
        "projects/<uuid:project_pk>/pages/<uuid:page_pk>/widgets/<uuid:pk>/",
        WidgetViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="canvas-widget-detail",
    ),
]
