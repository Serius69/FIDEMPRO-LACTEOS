"""
FindemproAI v2.0 — Canvas API Views (DRF)
API REST para el canvas visual. Prefijo: /api/v2/

Adaptado de la spec Flask → Django REST Framework:
  Blueprint   → DefaultRouter + ViewSet
  request.json → request.data
  jsonify()   → Response()
  abort(404)  → raise NotFound()
"""
import json
import time
import uuid
import logging

from django.db import transaction
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..canvas_models import (
    CanvasSimulationRun,
    InterfacePage,
    InterfaceWidget,
    ModelEdge,
    ModelNode,
    SimulationProject,
)
from ..canvas_serializers import (
    CanvasSimulationRunSerializer,
    InterfacePageSerializer,
    InterfaceWidgetSerializer,
    ModelEdgeSerializer,
    ModelNodePositionSerializer,
    ModelNodeSerializer,
    RiskAlertSerializer,
    SimulationProjectDetailSerializer,
    SimulationProjectListSerializer,
)
from ..core.model_compiler import ModelCompiler, ModelCompilerError
from ..models import RiskAlert

logger = logging.getLogger(__name__)


# ─── PROYECTOS ────────────────────────────────────────────────────────────────

class ProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD de proyectos de modelado visual.

    GET    /api/v2/projects/           → lista paginada
    POST   /api/v2/projects/           → crear con plantilla láctea
    GET    /api/v2/projects/{id}/      → detalle completo (nodos, edges, páginas)
    PUT    /api/v2/projects/{id}/      → actualizar metadatos / run_specs
    DELETE /api/v2/projects/{id}/      → eliminar en cascada
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        base = SimulationProject.objects.filter(user=self.request.user)
        if self.action == 'list':
            # Optimización lista: Count via JOIN (evita N+1) + Prefetch limitado para last_run
            return (
                base
                .annotate(
                    node_count_ann=Count('nodes', distinct=True),
                    edge_count_ann=Count('edges', distinct=True),
                )
                .prefetch_related(
                    Prefetch(
                        'runs',
                        queryset=CanvasSimulationRun.objects.order_by('-created_at'),
                        to_attr='latest_runs',
                    )
                )
                .order_by('-updated_at')
            )
        # Detalle: carga completa de nodos, edges y páginas
        return (
            base
            .prefetch_related('nodes', 'edges', 'pages__widgets', 'runs')
            .order_by('-updated_at')
        )

    def get_serializer_class(self):
        if self.action in ("list",):
            return SimulationProjectListSerializer
        return SimulationProjectDetailSerializer

    def perform_create(self, serializer):
        project = serializer.save(user=self.request.user)
        _seed_dairy_template(project)

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """Exporta el proyecto completo como JSON portable."""
        project = self.get_object()
        data = SimulationProjectDetailSerializer(project).data
        return Response(data)

    @action(detail=False, methods=["post"])
    def import_project(self, request):
        """Importa un proyecto desde JSON exportado previamente."""
        data = request.data
        required = ("name", "nodes", "edges")
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                {"error": f"Faltan campos: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            project = SimulationProject.objects.create(
                user=request.user,
                name=data.get("name", "Proyecto Importado"),
                description=data.get("description", ""),
                domain=data.get("domain", "dairy"),
                run_specs=data.get("run_specs", {}),
            )
            # Re-map IDs: los UUIDs del JSON original → nuevos UUIDs
            id_map = {}
            for n in data.get("nodes", []):
                old_id = n.pop("id", None)
                n.pop("project", None)
                node = ModelNode.objects.create(project=project, **{
                    k: v for k, v in n.items()
                    if k in [f.name for f in ModelNode._meta.get_fields() if hasattr(f, "name")]
                })
                if old_id:
                    id_map[old_id] = str(node.id)

            for e in data.get("edges", []):
                e.pop("id", None)
                src_id = id_map.get(str(e.get("source_node"))) or str(e.get("source_node"))
                tgt_id = id_map.get(str(e.get("target_node"))) or str(e.get("target_node"))
                try:
                    ModelEdge.objects.create(
                        project=project,
                        source_node_id=src_id,
                        target_node_id=tgt_id,
                        edge_type=e.get("edge_type", "causal"),
                        line_style=e.get("line_style", "solid"),
                        polarity=e.get("polarity"),
                        waypoints=e.get("waypoints", []),
                    )
                except Exception:
                    pass  # edge inválido se omite

        return Response(
            SimulationProjectDetailSerializer(project).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Marca el proyecto como publicado (URL pública de Interface Window)."""
        project = self.get_object()
        slug = str(project.id).replace("-", "")[:16]
        return Response({"public_url": f"/canvas/view/{slug}/", "project_id": str(project.id)})


# ─── NODOS DEL CANVAS ─────────────────────────────────────────────────────────

class NodeViewSet(viewsets.ModelViewSet):
    """
    CRUD de nodos para un proyecto específico.

    GET    /api/v2/projects/{pid}/nodes/
    POST   /api/v2/projects/{pid}/nodes/
    PUT    /api/v2/projects/{pid}/nodes/{id}/
    DELETE /api/v2/projects/{pid}/nodes/{id}/
    PUT    /api/v2/projects/{pid}/nodes/batch-position/
    """

    serializer_class = ModelNodeSerializer
    permission_classes = [IsAuthenticated]

    def _get_project(self):
        return get_object_or_404(
            SimulationProject,
            pk=self.kwargs["project_pk"],
            user=self.request.user,
        )

    def get_queryset(self):
        return ModelNode.objects.filter(project=self._get_project())

    def perform_create(self, serializer):
        serializer.save(project=self._get_project())

    @action(detail=False, methods=["put"], url_path="batch-position")
    def batch_position(self, request, project_pk=None):
        """
        Actualiza posiciones de múltiples nodos en una query.
        Body: [{id, position_x, position_y}, ...]
        """
        items_ser = ModelNodePositionSerializer(data=request.data, many=True)
        if not items_ser.is_valid():
            return Response(items_ser.errors, status=status.HTTP_400_BAD_REQUEST)

        project = self._get_project()
        updated = 0
        with transaction.atomic():
            for item in items_ser.validated_data:
                rows = ModelNode.objects.filter(
                    id=item["id"], project=project,
                ).update(position_x=item["position_x"], position_y=item["position_y"])
                updated += rows

        return Response({"updated": updated})


# ─── CONEXIONES ───────────────────────────────────────────────────────────────

class EdgeViewSet(viewsets.ModelViewSet):
    """
    CRUD de edges para un proyecto.

    GET    /api/v2/projects/{pid}/edges/
    POST   /api/v2/projects/{pid}/edges/
    DELETE /api/v2/projects/{pid}/edges/{id}/
    """

    serializer_class = ModelEdgeSerializer
    permission_classes = [IsAuthenticated]

    def _get_project(self):
        return get_object_or_404(
            SimulationProject,
            pk=self.kwargs["project_pk"],
            user=self.request.user,
        )

    def get_queryset(self):
        return ModelEdge.objects.filter(project=self._get_project()).select_related(
            "source_node", "target_node"
        )

    def perform_create(self, serializer):
        serializer.save(project=self._get_project())


# ─── SIMULACIÓN ───────────────────────────────────────────────────────────────

class SimulationRunView(APIView):
    """
    POST /api/v2/projects/{pid}/simulate/

    Compila el grafo y ejecuta simulación usando el motor existente.
    Body: {run_type: 'montecarlo'|'des'|'scenario', override_params: {...}, scenario: 'optimistic'|...}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_pk):
        project = get_object_or_404(SimulationProject, pk=project_pk, user=request.user)

        run_type = request.data.get("run_type", "montecarlo")
        override_params = request.data.get("override_params", {})
        scenario = request.data.get("scenario", "expected")

        nodes = list(project.nodes.values(
            "id", "node_type", "label", "equation", "initial_value",
            "units", "position_x", "position_y", "distribution_config",
        ))
        for n in nodes:
            n["id"] = str(n["id"])

        edges = list(project.edges.values(
            "id", "source_node_id", "target_node_id", "edge_type", "line_style", "polarity",
        ))
        for e in edges:
            e["id"] = str(e["id"])
            e["source_node_id"] = str(e["source_node_id"])
            e["target_node_id"] = str(e["target_node_id"])

        run_specs = {**project.run_specs, **override_params}

        try:
            compiler = ModelCompiler(nodes, edges, run_specs)
            compiled = compiler.compile()
        except ModelCompilerError as exc:
            return Response(
                {"error": str(exc), "type": "compilation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        t_start = time.time()
        results = {}
        stats = {}

        if run_type == "montecarlo":
            mc_config = compiler.compile_to_montecarlo_config()
            results, stats = _run_montecarlo(mc_config)

        elif run_type == "des":
            des_config = compiler.compile_to_des_config()
            results, stats = _run_des(des_config)

        elif run_type == "scenario":
            mc_config = compiler.compile_to_montecarlo_config()
            results, stats = _run_scenario(mc_config, scenario)

        duration_ms = int((time.time() - t_start) * 1000)

        run = CanvasSimulationRun.objects.create(
            project=project,
            run_type=run_type,
            parameters_snapshot=run_specs,
            results=results,
            statistics=stats,
            run_duration_ms=duration_ms,
            n_runs=run_specs.get("n_runs_montecarlo", 1000),
        )

        return Response({
            "run_id": str(run.id),
            "run_type": run_type,
            "results": results,
            "statistics": stats,
            "duration_ms": duration_ms,
            "compiled_model_summary": {
                "n_stocks": len(compiled["stocks"]),
                "n_flows": len(compiled["flows"]),
                "n_converters": len(compiled["converters"]),
            },
        }, status=status.HTTP_200_OK)


class SimulationLiveUpdateView(APIView):
    """
    POST /api/v2/projects/{pid}/simulate/live-update/

    Actualiza parámetros en tiempo real (< 500 ms para N=1000).
    Body: {param_changes: {variable_label: new_value, ...}}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_pk):
        project = get_object_or_404(SimulationProject, pk=project_pk, user=request.user)
        param_changes = request.data.get("param_changes", {})

        if not param_changes:
            return Response(
                {"error": "param_changes vacío"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Aplicar cambios a los nodos afectados en memoria (sin persistir)
        nodes = list(project.nodes.values(
            "id", "node_type", "label", "equation", "initial_value",
            "units", "distribution_config",
        ))
        for n in nodes:
            n["id"] = str(n["id"])
            label = n["label"]
            if label in param_changes:
                if n["node_type"] == "stock":
                    n["initial_value"] = param_changes[label]
                else:
                    # Overwrite como constante en ecuación
                    n["equation"] = str(param_changes[label])

        edges = list(project.edges.values(
            "id", "source_node_id", "target_node_id", "edge_type", "line_style", "polarity",
        ))
        for e in edges:
            e["id"] = str(e["id"])
            e["source_node_id"] = str(e["source_node_id"])
            e["target_node_id"] = str(e["target_node_id"])

        run_specs = {**project.run_specs, "n_runs_montecarlo": 200}  # rápido

        t_start = time.time()
        try:
            compiler = ModelCompiler(nodes, edges, run_specs)
            mc_config = compiler.compile_to_montecarlo_config()
            results, stats = _run_montecarlo(mc_config)
            affected = compiler.get_affected_variables(list(param_changes.keys()))
        except ModelCompilerError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        duration_ms = int((time.time() - t_start) * 1000)
        return Response({
            "updated_variables": list(param_changes.keys()),
            "affected_downstream": affected,
            "delta_results": results,
            "processing_time_ms": duration_ms,
        })


class SimulationValidateView(APIView):
    """
    POST /api/v2/projects/{pid}/simulate/validate/

    Valida el modelo antes de simular: ciclos, ecuaciones faltantes, tipos de nodos.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_pk):
        project = get_object_or_404(SimulationProject, pk=project_pk, user=request.user)

        nodes = list(project.nodes.values(
            "id", "node_type", "label", "equation", "initial_value", "units",
        ))
        for n in nodes:
            n["id"] = str(n["id"])

        edges = list(project.edges.values(
            "id", "source_node_id", "target_node_id", "edge_type", "line_style", "polarity",
        ))
        for e in edges:
            e["id"] = str(e["id"])
            e["source_node_id"] = str(e["source_node_id"])
            e["target_node_id"] = str(e["target_node_id"])

        compiler = ModelCompiler(nodes, edges, project.run_specs)
        errors = compiler.validate()
        warnings = _compute_warnings(nodes, edges)

        return Response({
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "node_count": len(nodes),
            "edge_count": len(edges),
        })


class CausalDiagramView(APIView):
    """
    GET /api/v2/projects/{pid}/simulate/causal-diagram/

    Retorna datos del Causal Loop Diagram (Map View) en formato Cytoscape.js.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_pk):
        project = get_object_or_404(SimulationProject, pk=project_pk, user=request.user)

        nodes = list(project.nodes.values(
            "id", "node_type", "label", "position_x", "position_y",
        ))
        for n in nodes:
            n["id"] = str(n["id"])

        edges = list(project.edges.values(
            "id", "source_node_id", "target_node_id", "edge_type", "line_style", "polarity",
        ))
        for e in edges:
            e["id"] = str(e["id"])
            e["source_node_id"] = str(e["source_node_id"])
            e["target_node_id"] = str(e["target_node_id"])

        compiler = ModelCompiler(nodes, edges, project.run_specs)
        cld_data = compiler.generate_causal_loop_diagram()
        return Response(cld_data)


class SensitivityAnalysisView(APIView):
    """
    POST /api/v2/projects/{pid}/simulate/sensitivity/

    Análisis de sensibilidad OAT (One-At-a-Time).
    Varía cada parámetro estocástico ±variation_pct y mide el impacto en utilidad.
    Devuelve datos para tornado chart ApexCharts.

    Si n_variables_estocásticas > 10 → encola tarea Celery y devuelve task_id (202).
    Si n_variables_estocásticas ≤ 10 → corre sincrónicamente y devuelve resultados (200).

    Body (todos opcionales):
        variation_pct float  — variación relativa (default: 0.20 = 20%)
        n_runs        int    — escenarios MC por variante (default: 500)
        seed          int    — semilla aleatoria (default: del proyecto)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, project_pk):
        project = get_object_or_404(SimulationProject, pk=project_pk, user=request.user)

        variation_pct = float(request.data.get('variation_pct', 0.20))
        n_runs = int(request.data.get('n_runs', 500))
        seed = request.data.get('seed', project.run_specs.get('random_seed'))

        if not 0.01 <= variation_pct <= 0.50:
            return Response(
                {'error': 'variation_pct debe estar entre 0.01 y 0.50'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not 10 <= n_runs <= 10_000:
            return Response(
                {'error': 'n_runs debe estar entre 10 y 10 000'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nodes = list(project.nodes.values(
            'id', 'node_type', 'label', 'equation', 'initial_value',
            'units', 'distribution_config',
        ))
        for n in nodes:
            n['id'] = str(n['id'])

        n_stochastic = sum(1 for n in nodes if n.get('distribution_config'))

        if n_stochastic > 10:
            from simulate.tasks import run_sensitivity_async
            task = run_sensitivity_async.delay(
                project_id=str(project.id),
                variation_pct=variation_pct,
                n_runs=n_runs,
                seed=seed,
            )
            return Response(
                {
                    'status': 'queued',
                    'task_id': task.id,
                    'n_stochastic_variables': n_stochastic,
                    'message': (
                        f'Análisis de {n_stochastic} variables enviado a cola. '
                        f'Consulta el resultado con task_id.'
                    ),
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # Ejecución síncrona para ≤ 10 variables
        from simulate.services.sensitivity_service import SensitivityService

        edges = list(project.edges.values(
            'id', 'source_node_id', 'target_node_id', 'edge_type',
        ))
        for e in edges:
            e['id'] = str(e['id'])
            e['source_node_id'] = str(e['source_node_id'])
            e['target_node_id'] = str(e['target_node_id'])

        t0 = time.time()
        service = SensitivityService()
        try:
            results = service.run_oat(
                nodes=nodes,
                edges=edges,
                run_specs=project.run_specs,
                variation_pct=variation_pct,
                n_runs=n_runs,
                seed=seed,
            )
        except ValueError as exc:
            return Response({"error": str(exc), "code": "financial_inputs_required"}, status=status.HTTP_400_BAD_REQUEST)
        duration_ms = int((time.time() - t0) * 1000)

        baseline_profit = results[0].baseline_mean if results else None
        chart_data = service.to_apexcharts(results, variation_pct, baseline_profit)

        return Response({
            'variation_pct': variation_pct,
            'n_runs': n_runs,
            'n_stochastic_variables': n_stochastic,
            'duration_ms': duration_ms,
            'tornado_chart': chart_data,
        })


class RiskAlertViewSet(viewsets.ModelViewSet):
    """
    CRUD de alertas de riesgo VaR/CVaR para el usuario autenticado.

    GET    /api/v2/alerts/           → lista de alertas del usuario
    POST   /api/v2/alerts/           → crear nueva alerta
    GET    /api/v2/alerts/{id}/      → detalle
    PUT    /api/v2/alerts/{id}/      → actualizar
    PATCH  /api/v2/alerts/{id}/      → actualización parcial
    DELETE /api/v2/alerts/{id}/      → eliminar
    """

    serializer_class = RiskAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RiskAlert.objects.filter(user=self.request.user).select_related('fk_product')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SimulationRunListView(APIView):
    """
    GET  /api/v2/projects/{pid}/runs/          → historial de corridas
    GET  /api/v2/projects/{pid}/runs/{rid}/    → detalle de una corrida
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, project_pk, run_pk=None):
        project = get_object_or_404(SimulationProject, pk=project_pk, user=request.user)

        if run_pk:
            run = get_object_or_404(CanvasSimulationRun, pk=run_pk, project=project)
            return Response(CanvasSimulationRunSerializer(run).data)

        runs = project.runs.all()[:50]
        return Response(CanvasSimulationRunSerializer(runs, many=True).data)


# ─── INTERFACE WINDOW ─────────────────────────────────────────────────────────

class PageViewSet(viewsets.ModelViewSet):
    """CRUD de páginas de la Interface Window."""

    serializer_class = InterfacePageSerializer
    permission_classes = [IsAuthenticated]

    def _get_project(self):
        return get_object_or_404(
            SimulationProject,
            pk=self.kwargs["project_pk"],
            user=self.request.user,
        )

    def get_queryset(self):
        return InterfacePage.objects.filter(project=self._get_project()).prefetch_related("widgets")

    def perform_create(self, serializer):
        project = self._get_project()
        max_order = project.pages.count()
        serializer.save(project=project, page_order=max_order)


class WidgetViewSet(viewsets.ModelViewSet):
    """CRUD de widgets dentro de una página."""

    serializer_class = InterfaceWidgetSerializer
    permission_classes = [IsAuthenticated]

    def _get_page(self):
        return get_object_or_404(
            InterfacePage,
            pk=self.kwargs["page_pk"],
            project__user=self.request.user,
        )

    def get_queryset(self):
        return InterfaceWidget.objects.filter(page=self._get_page())

    def perform_create(self, serializer):
        serializer.save(page=self._get_page())


# ─── HELPERS INTERNOS ─────────────────────────────────────────────────────────

def _run_montecarlo(mc_config: dict):
    """
    Llama al motor Monte Carlo existente de FindemproAI.
    Retorna (results_dict, stats_dict).
    """
    required = ("unit_price", "unit_cost", "fixed_costs")
    missing = [key for key in required if mc_config.get(key) is None]
    if missing:
        return (
            {"type": "incomplete", "reason": "financial_inputs_required", "missing": missing},
            {"status": "incomplete", "missing": missing},
        )
    try:
        from ..core.monte_carlo import MonteCarloConfig, ScenarioGenerator, aggregate_results

        n_runs = mc_config.get("n_runs", 1000)
        dt = mc_config.get("dt", 1)
        time_steps = mc_config.get("time_steps", 365)
        seed = mc_config.get("seed")

        variables = mc_config.get("variables", {})
        if not variables:
            # Sin distribuciones definidas → simulación determinística
            return {"type": "deterministic", "time_steps": time_steps}, {}

        # Construir MonteCarloConfig desde el dict compilado
        first_var = next(iter(variables.values()))
        config = MonteCarloConfig(
            distribution_type=first_var.get("distribution", "normal"),
            distribution_params=first_var.get("params", {}),
            n_scenarios=n_runs,
            seed=seed,
        )
        gen = ScenarioGenerator(config)
        scenarios = [gen.generate(0) for _ in range(n_runs)]

        unit_price = float(mc_config["unit_price"])
        unit_cost = float(mc_config["unit_cost"])
        fixed_costs = float(mc_config["fixed_costs"])
        profits = [s.demand * (unit_price - unit_cost) - fixed_costs for s in scenarios]
        demands = [s.demand for s in scenarios]
        revenues = [s.demand * unit_price for s in scenarios]

        agg = aggregate_results(profits, demands, revenues, config)
        stats = {
            "mean_profit": agg.mean_profit,
            "std_profit": agg.std_profit,
            "p5_profit": agg.p5_profit,
            "p95_profit": agg.p95_profit,
            "probability_positive": agg.probability_positive,
        }
        return {"scenarios": len(scenarios), "type": "montecarlo"}, stats

    except Exception as exc:
        logger.warning("Motor MC no disponible: %s — usando simulación mínima", exc)
        return _minimal_montecarlo(mc_config)


def _minimal_montecarlo(mc_config: dict):
    """Return a truthful incomplete result instead of fabricated economics."""
    return (
        {"type": "incomplete", "reason": "canonical_engine_unavailable"},
        {"status": "incomplete", "missing": ["canonical_monte_carlo_engine"]},
    )


def _run_des(des_config: dict):
    """Llama al motor DES existente (discrete_engine.py)."""
    try:
        from ..core.discrete_engine import DiscreteEventEngine, CompanyConfig

        config = build_config_from_des_dict(des_config)
        if config is None:
            return {"type": "incomplete", "reason": "des_adapter_not_configured"}, {"status": "incomplete", "missing": ["des_company_config"]}
        engine = DiscreteEventEngine(config)
        results = []
        for t in range(des_config.get("time_steps", 365)):
            state = engine.step()
            results.append(state)

        return {"type": "des", "time_steps": len(results), "final_state": results[-1] if results else {}}, {}

    except Exception as exc:
        logger.warning("Motor DES no disponible: %s", exc)
        return {"type": "des_unavailable", "error": str(exc)}, {}


def build_config_from_des_dict(des_config: dict):
    """Construye CompanyConfig desde des_config (interfaz entre compiler y engine)."""
    # This legacy canvas adapter has no lossless mapping to CompanyConfig yet.
    # Returning None is handled as an explicit incomplete result above; never
    # silently run a differently parameterized simulation.
    return None


def _run_scenario(mc_config: dict, scenario: str):
    """Ejecuta escenario solo con entradas financieras explícitas."""
    import numpy as np

    required = ("base_demand", "unit_price", "unit_cost", "fixed_costs")
    missing = [key for key in required if mc_config.get(key) is None]
    if missing:
        return (
            {"type": "incomplete", "reason": "financial_inputs_required", "missing": missing},
            {"status": "incomplete", "missing": missing},
        )

    multipliers = {"pessimistic": 0.7, "expected": 1.0, "optimistic": 1.3}
    factor = multipliers.get(scenario, 1.0)

    n_runs = mc_config.get("n_runs", 1000)
    seed = mc_config.get("seed")
    rng = np.random.default_rng(seed)

    base_demand = float(mc_config["base_demand"])
    unit_price = float(mc_config["unit_price"])
    unit_cost = float(mc_config["unit_cost"])
    fixed_costs = float(mc_config["fixed_costs"])
    demand_std = float(mc_config.get("demand_std", base_demand * 0.15))
    demands = rng.normal(base_demand * factor, demand_std, n_runs)
    profits = demands * (unit_price - unit_cost) - fixed_costs

    return (
        {"type": "scenario", "scenario": scenario, "n_runs": n_runs},
        {
            "mean_profit": float(profits.mean()),
            "std_profit": float(profits.std()),
            "p5_profit": float(np.percentile(profits, 5)),
            "p95_profit": float(np.percentile(profits, 95)),
            "scenario_factor": factor,
        },
    )


def _compute_warnings(nodes: list, edges: list) -> list:
    """Warnings no bloqueantes (no impiden simular pero son buenas prácticas)."""
    warnings = []
    node_ids = {n["id"] for n in nodes}
    connected_ids = set()
    for e in edges:
        connected_ids.add(e["source_node_id"])
        connected_ids.add(e["target_node_id"])

    for node in nodes:
        if node["id"] not in connected_ids and node["node_type"] != "text_box":
            warnings.append(
                f"Nodo '{node['label']}' no tiene conexiones — puede estar aislado"
            )
        if node["node_type"] in ("flow", "converter") and node.get("equation"):
            eq = node["equation"]
            if any(c in eq for c in [";", "import", "__"]):
                warnings.append(
                    f"Nodo '{node['label']}': ecuación contiene sintaxis no permitida"
                )

    stocks = [n for n in nodes if n["node_type"] == "stock"]
    if not stocks:
        warnings.append("El modelo no tiene stocks — considera añadir al menos uno")

    return warnings


def _seed_dairy_template(project: SimulationProject):
    """
    Crea nodos plantilla para PYME láctea boliviana.
    Llamado automáticamente al crear un nuevo proyecto con domain='dairy'.
    """
    if project.domain != "dairy":
        return

    with transaction.atomic():
        node_defs = [
            # STOCKS
            dict(node_type="stock", label="Inventario Leche Cruda",
                 initial_value=1000, units="litros", position_x=200, position_y=200,
                 equation="Inventario_Leche_Cruda(t-DT) + (tasa_recepcion - tasa_procesamiento) * DT"),
            dict(node_type="stock", label="Inventario Productos Terminados",
                 initial_value=500, units="unidades", position_x=500, position_y=200,
                 equation="Inventario_Productos(t-DT) + (tasa_produccion - tasa_ventas) * DT"),
            dict(node_type="stock", label="Caja Disponible",
                 initial_value=50000, units="BOB", position_x=800, position_y=200,
                 equation="Caja(t-DT) + (ingresos_ventas - costos_operativos - costos_insumos) * DT"),
            # FLOWS
            dict(node_type="flow", label="tasa_recepcion", units="litros/dia",
                 position_x=100, position_y=200,
                 equation="demanda_leche_cruda * factor_estacionalidad",
                 distribution_config={"dist_type": "triangular", "params": {"low": 800, "mode": 1000, "high": 1300}}),
            dict(node_type="flow", label="tasa_produccion", units="unidades/dia",
                 position_x=350, position_y=200,
                 equation="tasa_procesamiento * rendimiento_conversion"),
            dict(node_type="flow", label="tasa_ventas", units="unidades/dia",
                 position_x=650, position_y=200,
                 equation="demanda_productos * MIN(1, Inventario_Productos / demanda_productos)",
                 distribution_config={"dist_type": "normal", "params": {"mean": 450, "std": 80}}),
            # CONVERTERS
            dict(node_type="converter", label="precio_leche_cruda", units="BOB/litro",
                 position_x=200, position_y=380, equation="3.80"),
            dict(node_type="converter", label="precio_venta_producto", units="BOB/unidad",
                 position_x=500, position_y=380, equation="12.50"),
            dict(node_type="converter", label="factor_estacionalidad", units="adimensional",
                 position_x=100, position_y=380, equation="1.0",
                 distribution_config={"dist_type": "uniform", "params": {"low": 0.85, "high": 1.20}}),
            dict(node_type="converter", label="rendimiento_conversion", units="unidades/litro",
                 position_x=350, position_y=380, equation="0.92"),
            dict(node_type="converter", label="costo_operativo_fijo", units="BOB/dia",
                 position_x=800, position_y=380, equation="2500"),
            dict(node_type="converter", label="ingresos_ventas", units="BOB/dia",
                 position_x=700, position_y=100, equation="tasa_ventas * precio_venta_producto"),
        ]

        created_nodes = {}
        for nd in node_defs:
            node = ModelNode.objects.create(project=project, **nd)
            created_nodes[nd["label"]] = node

        # Edges semánticos del modelo lácteo
        edge_defs = [
            ("tasa_recepcion", "Inventario Leche Cruda", "flow", "+"),
            ("Inventario Leche Cruda", "tasa_produccion", "flow", None),
            ("tasa_produccion", "Inventario Productos Terminados", "flow", "+"),
            ("Inventario Productos Terminados", "tasa_ventas", "flow", None),
            ("tasa_ventas", "ingresos_ventas", "info", "+"),
            ("ingresos_ventas", "Caja Disponible", "info", "+"),
            ("factor_estacionalidad", "tasa_recepcion", "causal", "+"),
            ("precio_venta_producto", "ingresos_ventas", "causal", "+"),
            ("costo_operativo_fijo", "Caja Disponible", "causal", "-"),
            ("rendimiento_conversion", "tasa_produccion", "causal", "+"),
        ]

        for src_label, tgt_label, etype, polarity in edge_defs:
            src = created_nodes.get(src_label)
            tgt = created_nodes.get(tgt_label)
            if src and tgt:
                ModelEdge.objects.create(
                    project=project,
                    source_node=src,
                    target_node=tgt,
                    edge_type=etype,
                    polarity=polarity,
                )

        # Páginas de Interface Window por defecto
        page_defs = [
            ("Modelo de Demanda", 0),
            ("Simulación Flujo de Caja", 1),
            ("Escenarios", 2),
            ("KPIs Financieros", 3),
        ]
        for title, order in page_defs:
            InterfacePage.objects.create(project=project, title=title, page_order=order)
