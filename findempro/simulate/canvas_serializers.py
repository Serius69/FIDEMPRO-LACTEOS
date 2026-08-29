"""
DRF serializers for FindemproAI v2.0 canvas models.
"""
from rest_framework import serializers
from .canvas_models import (
    SimulationProject,
    ModelNode,
    ModelEdge,
    InterfacePage,
    InterfaceWidget,
    CanvasSimulationRun,
)
from .models import RiskAlert


class ModelNodeSerializer(serializers.ModelSerializer):
    node_type_display = serializers.CharField(source="get_node_type_display", read_only=True)

    class Meta:
        model = ModelNode
        fields = [
            "id", "project", "node_type", "node_type_display", "label",
            "equation", "initial_value", "units",
            "position_x", "position_y", "width", "height",
            "style", "distribution_config", "ghost_of_node",
            "metadata", "created_at",
        ]
        read_only_fields = [
            "id", "project", "results", "statistics", "run_duration_ms", "n_runs",
            "status", "progress", "error", "created_at",
        ]

    def validate_distribution_config(self, value):
        if value is None:
            return value
        if "dist_type" not in value:
            raise serializers.ValidationError("distribution_config debe incluir 'dist_type'")
        valid = ("normal", "lognormal", "triangular", "uniform", "gamma", "beta", "weibull")
        if value["dist_type"] not in valid:
            raise serializers.ValidationError(
                f"dist_type inválido. Opciones: {', '.join(valid)}"
            )
        if "params" not in value or not isinstance(value["params"], dict):
            raise serializers.ValidationError("distribution_config debe incluir 'params' como dict")
        return value

    def validate_node_type(self, value):
        if value in ("ghost",) and not self.initial_data.get("ghost_of_node"):
            raise serializers.ValidationError("Nodo tipo 'ghost' requiere 'ghost_of_node'")
        return value


class ModelNodePositionSerializer(serializers.Serializer):
    """Para batch-update de posiciones."""
    id = serializers.UUIDField()
    position_x = serializers.FloatField()
    position_y = serializers.FloatField()


class ModelEdgeSerializer(serializers.ModelSerializer):
    source_label = serializers.CharField(source="source_node.label", read_only=True)
    target_label = serializers.CharField(source="target_node.label", read_only=True)

    class Meta:
        model = ModelEdge
        fields = [
            "id", "project", "source_node", "target_node",
            "source_label", "target_label",
            "edge_type", "line_style", "polarity", "waypoints", "metadata",
        ]
        read_only_fields = ["id", "source_label", "target_label"]

    def validate(self, data):
        src = data.get("source_node")
        tgt = data.get("target_node")
        if src and tgt and src == tgt:
            raise serializers.ValidationError("Un nodo no puede conectarse consigo mismo")
        if data.get("edge_type") == "flow":
            if src and src.node_type not in ("stock", "flow"):
                raise serializers.ValidationError(
                    "Edge tipo 'flow': source debe ser stock o flow"
                )
            if tgt and tgt.node_type not in ("stock", "flow"):
                raise serializers.ValidationError(
                    "Edge tipo 'flow': target debe ser stock o flow"
                )
        return data


class InterfaceWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceWidget
        fields = [
            "id", "page", "widget_type", "label",
            "linked_node", "linked_variable",
            "config", "position_x", "position_y", "width", "height", "style",
        ]
        read_only_fields = ["id"]


class InterfacePageSerializer(serializers.ModelSerializer):
    widgets = InterfaceWidgetSerializer(many=True, read_only=True)

    class Meta:
        model = InterfacePage
        fields = ["id", "project", "title", "page_order", "background_color", "metadata", "widgets"]
        read_only_fields = ["id"]


class CanvasSimulationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanvasSimulationRun
        fields = [
            "id", "project", "run_type",
            "parameters_snapshot", "results", "statistics",
            "run_duration_ms", "n_runs", "status", "progress", "error", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RunSpecsSerializer(serializers.Serializer):
    start_time = serializers.FloatField(default=0)
    stop_time = serializers.FloatField(default=365)
    dt = serializers.FloatField(default=1.0, min_value=0.001)
    time_units = serializers.CharField(default="dias", max_length=20)
    n_runs_montecarlo = serializers.IntegerField(default=1000, min_value=1, max_value=100000)
    integration_method = serializers.ChoiceField(
        choices=["euler", "runge_kutta_4", "midpoint"], default="euler"
    )
    random_seed = serializers.IntegerField(allow_null=True, required=False)


class SimulationProjectListSerializer(serializers.ModelSerializer):
    node_count = serializers.SerializerMethodField()
    edge_count = serializers.SerializerMethodField()
    last_run = serializers.SerializerMethodField()

    class Meta:
        model = SimulationProject
        fields = [
            "id", "name", "description", "domain",
            "run_specs", "created_at", "updated_at",
            "node_count", "edge_count", "last_run",
        ]

    def get_node_count(self, obj):
        # Uses Count annotation when the queryset is optimized in get_queryset()
        if hasattr(obj, 'node_count_ann'):
            return obj.node_count_ann
        return obj.nodes.count()

    def get_edge_count(self, obj):
        # Uses Count annotation when the queryset is optimized in get_queryset()
        if hasattr(obj, 'edge_count_ann'):
            return obj.edge_count_ann
        return obj.edges.count()

    def get_last_run(self, obj):
        # Uses Prefetch(to_attr='latest_runs') when queryset is optimized
        latest_runs = getattr(obj, 'latest_runs', None)
        if latest_runs is not None:
            run = latest_runs[0] if latest_runs else None
        else:
            run = obj.runs.order_by('-created_at').first()
        if run:
            return {"id": str(run.id), "run_type": run.run_type, "created_at": run.created_at}
        return None


class RiskAlertSerializer(serializers.ModelSerializer):
    """CRUD serializer para RiskAlert. El usuario se toma del request, no del payload."""

    is_triggered_now = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RiskAlert
        fields = [
            'id', 'fk_product', 'var_threshold', 'cvar_threshold',
            'email', 'is_active', 'created_at', 'updated_at',
            'is_triggered_now',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_triggered_now']

    def get_is_triggered_now(self, obj):
        return None  # Solo se calcula al ejecutar una simulación

    def validate_var_threshold(self, value):
        if value is None:
            raise serializers.ValidationError('var_threshold es obligatorio.')
        return value


class SimulationProjectDetailSerializer(serializers.ModelSerializer):
    nodes = ModelNodeSerializer(many=True, read_only=True)
    edges = ModelEdgeSerializer(many=True, read_only=True)
    pages = InterfacePageSerializer(many=True, read_only=True)
    run_specs = RunSpecsSerializer()

    class Meta:
        model = SimulationProject
        fields = [
            "id", "name", "description", "domain",
            "run_specs", "created_at", "updated_at",
            "nodes", "edges", "pages",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        run_specs_data = validated_data.pop("run_specs", None)
        if run_specs_data:
            instance.run_specs = run_specs_data
        return super().update(instance, validated_data)
