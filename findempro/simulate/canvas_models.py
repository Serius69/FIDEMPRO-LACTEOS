"""
Django ORM models for FindemproAI v2.0 visual canvas system.
Equivalent to the v2_model_canvas.sql schema but managed by Django migrations.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

_DEFAULT_RUN_SPECS = {
    "start_time": 0,
    "stop_time": 365,
    "dt": 1,
    "time_units": "dias",
    "n_runs_montecarlo": 1000,
    "integration_method": "euler",
    "random_seed": None,
}


class SimulationProject(models.Model):
    """Proyecto de modelado visual. Agrupa nodos, edges, páginas y corridas."""

    DOMAIN_CHOICES = [
        ("dairy", "Sector Lácteo"),
        ("agro", "Agroindustrial"),
        ("retail", "Retail"),
        ("services", "Servicios"),
        ("manufacturing", "Manufactura"),
        ("generic", "Genérico"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name="canvas_projects",
    )
    organization = models.ForeignKey(
        "tenancy.Organization",
        on_delete=models.PROTECT,
        related_name="simulation_projects",
        null=True,
        blank=True,
        db_index=True,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES, default="dairy")
    run_specs = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "simulate"
        ordering = ["-updated_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(organization__isnull=False),
                name="canvas_project_requires_organization",
            )
        ]

    def __str__(self):
        return self.name

    def get_default_run_specs(self):
        return _DEFAULT_RUN_SPECS.copy()

    def save(self, *args, **kwargs):
        if self.organization_id is None and self.user_id:
            from tenancy.services import ensure_default_organization

            self.organization = ensure_default_organization(self.user)
        if not self.run_specs:
            self.run_specs = self.get_default_run_specs()
        super().save(*args, **kwargs)


class ModelNode(models.Model):
    """Nodo del canvas visual (stock, flow, converter, ghost, text_box)."""

    NODE_TYPES = [
        ("stock", "Stock"),
        ("flow", "Flow"),
        ("converter", "Converter"),
        ("connector", "Connector"),
        ("ghost", "Ghost"),
        ("text_box", "Text Box"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        SimulationProject, on_delete=models.CASCADE, related_name="nodes",
    )
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    label = models.CharField(max_length=100)
    equation = models.TextField(blank=True, null=True)
    initial_value = models.FloatField(null=True, blank=True)
    units = models.CharField(max_length=50, blank=True)
    position_x = models.FloatField(default=100.0)
    position_y = models.FloatField(default=100.0)
    width = models.FloatField(default=120.0)
    height = models.FloatField(default=60.0)
    style = models.JSONField(default=dict, blank=True)
    distribution_config = models.JSONField(
        null=True, blank=True,
        help_text="Config de distribución: {dist_type, params}",
    )
    ghost_of_node = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ghost_instances",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "simulate"
        indexes = [models.Index(fields=["project"])]

    def __str__(self):
        return f"{self.node_type}:{self.label}"


class ModelEdge(models.Model):
    """Conexión dirigida entre dos nodos del canvas."""

    EDGE_TYPES = [
        ("causal", "Causal"),
        ("flow", "Flow"),
        ("info", "Info"),
    ]
    LINE_STYLES = [
        ("solid", "Sólido"),
        ("dashed", "Punteado"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        SimulationProject, on_delete=models.CASCADE, related_name="edges",
    )
    source_node = models.ForeignKey(
        ModelNode, on_delete=models.CASCADE, related_name="outgoing_edges",
    )
    target_node = models.ForeignKey(
        ModelNode, on_delete=models.CASCADE, related_name="incoming_edges",
    )
    edge_type = models.CharField(max_length=20, choices=EDGE_TYPES, default="causal")
    line_style = models.CharField(max_length=20, choices=LINE_STYLES, default="solid")
    polarity = models.CharField(max_length=5, blank=True, null=True)
    waypoints = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "simulate"
        indexes = [models.Index(fields=["project"])]

    def __str__(self):
        return f"{self.source_node.label} → {self.target_node.label}"


class InterfacePage(models.Model):
    """Página de la Interface Window (dashboard paginado interactivo)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        SimulationProject, on_delete=models.CASCADE, related_name="pages",
    )
    title = models.CharField(max_length=100)
    page_order = models.IntegerField(default=0)
    background_color = models.CharField(max_length=20, default="#0f172a")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "simulate"
        ordering = ["page_order"]

    def __str__(self):
        return f"{self.project.name} / {self.title}"


class InterfaceWidget(models.Model):
    """Widget interactivo en una página de la Interface Window."""

    WIDGET_TYPES = [
        ("slider", "Slider"),
        ("knob", "Knob"),
        ("dial", "Dial"),
        ("run_button", "Run Button"),
        ("stop_button", "Stop Button"),
        ("reset_button", "Reset Button"),
        ("time_slider", "Time Slider"),
        ("graph_output", "Graph Output"),
        ("table_output", "Table Output"),
        ("gauge", "Gauge"),
        ("numeric_display", "Numeric Display"),
        ("scenario_toggle", "Scenario Toggle"),
        ("text_annotation", "Text Annotation"),
        ("page_nav", "Page Navigation"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(
        InterfacePage, on_delete=models.CASCADE, related_name="widgets",
    )
    widget_type = models.CharField(max_length=30, choices=WIDGET_TYPES)
    label = models.CharField(max_length=100, blank=True)
    linked_node = models.ForeignKey(
        ModelNode, on_delete=models.SET_NULL, null=True, blank=True,
    )
    linked_variable = models.CharField(max_length=100, blank=True)
    config = models.JSONField(default=dict, blank=True)
    position_x = models.FloatField(default=50.0)
    position_y = models.FloatField(default=50.0)
    width = models.FloatField(default=200.0)
    height = models.FloatField(default=100.0)
    style = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = "simulate"
        indexes = [models.Index(fields=["page"])]

    def __str__(self):
        return f"{self.widget_type}:{self.label}"


class CanvasSimulationRun(models.Model):
    """Resultado cacheado de una corrida de simulación del canvas."""

    RUN_TYPES = [
        ("montecarlo", "Monte Carlo"),
        ("des", "Discrete Event Simulation"),
        ("sensitivity", "Sensitivity Analysis"),
        ("scenario", "Scenario"),
    ]
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        SimulationProject, on_delete=models.CASCADE, related_name="runs",
    )
    run_type = models.CharField(max_length=20, choices=RUN_TYPES, default="montecarlo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued", db_index=True)
    progress = models.PositiveSmallIntegerField(default=0)
    error = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=180, blank=True)
    parameters_snapshot = models.JSONField(null=True, blank=True)
    results = models.JSONField(null=True, blank=True)
    statistics = models.JSONField(null=True, blank=True)
    run_duration_ms = models.IntegerField(null=True, blank=True)
    n_runs = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "simulate"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["project", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="uniq_canvas_run_idempotency",
            )
        ]

    def __str__(self):
        return f"{self.project.name} / {self.run_type} @ {self.created_at:%Y-%m-%d %H:%M}"
