"""
Dataclasses de dominio para FindemproAI v2.0 — canvas visual.
Usadas por el ModelCompiler y la capa de servicios; independientes del ORM.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class NodeType(Enum):
    STOCK = "stock"
    FLOW = "flow"
    CONVERTER = "converter"
    CONNECTOR = "connector"
    GHOST = "ghost"
    TEXT_BOX = "text_box"


class EdgeType(Enum):
    CAUSAL = "causal"
    FLOW = "flow"
    INFO = "info"


class WidgetType(Enum):
    SLIDER = "slider"
    KNOB = "knob"
    GRAPH_OUTPUT = "graph_output"
    GAUGE = "gauge"
    NUMERIC_DISPLAY = "numeric_display"
    RUN_BUTTON = "run_button"
    STOP_BUTTON = "stop_button"
    RESET_BUTTON = "reset_button"
    TIME_SLIDER = "time_slider"
    SCENARIO_TOGGLE = "scenario_toggle"
    TABLE_OUTPUT = "table_output"
    PAGE_NAV = "page_nav"


@dataclass
class DistributionConfig:
    """
    Configuración de distribución probabilística para un nodo.

    dist_type: 'normal' | 'lognormal' | 'triangular' | 'uniform' | 'gamma' | 'beta' | 'weibull'
    params keys:
      normal      → mean, std
      lognormal   → mu, sigma
      triangular  → low, mode, high
      uniform     → low, high
      gamma       → shape, scale
      beta        → alpha, beta, low, high
      weibull     → shape, scale
    """

    dist_type: str
    params: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"dist_type": self.dist_type, "params": self.params}

    @classmethod
    def from_dict(cls, data: Dict) -> "DistributionConfig":
        return cls(dist_type=data["dist_type"], params=data.get("params", {}))


@dataclass
class ModelNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    node_type: NodeType = NodeType.CONVERTER
    label: str = "Nueva Variable"
    equation: Optional[str] = None
    initial_value: Optional[float] = None
    units: Optional[str] = None
    position_x: float = 100.0
    position_y: float = 100.0
    width: float = 120.0
    height: float = 60.0
    style: Dict[str, Any] = field(default_factory=dict)
    distribution_config: Optional[DistributionConfig] = None
    ghost_of_node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "equation": self.equation,
            "initial_value": self.initial_value,
            "units": self.units,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "width": self.width,
            "height": self.height,
            "style": self.style,
            "distribution_config": self.distribution_config.to_dict() if self.distribution_config else None,
            "ghost_of_node_id": self.ghost_of_node_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_orm(cls, orm_node) -> "ModelNode":
        dist = None
        if orm_node.distribution_config:
            dist = DistributionConfig.from_dict(orm_node.distribution_config)
        return cls(
            id=str(orm_node.id),
            project_id=str(orm_node.project_id),
            node_type=NodeType(orm_node.node_type),
            label=orm_node.label,
            equation=orm_node.equation,
            initial_value=orm_node.initial_value,
            units=orm_node.units or "",
            position_x=orm_node.position_x,
            position_y=orm_node.position_y,
            width=orm_node.width,
            height=orm_node.height,
            style=orm_node.style or {},
            distribution_config=dist,
            ghost_of_node_id=str(orm_node.ghost_of_node_id) if orm_node.ghost_of_node_id else None,
            metadata=orm_node.metadata or {},
        )


@dataclass
class ModelEdge:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    source_node_id: str = ""
    target_node_id: str = ""
    edge_type: EdgeType = EdgeType.CAUSAL
    line_style: str = "solid"
    polarity: Optional[str] = None
    waypoints: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "edge_type": self.edge_type.value,
            "line_style": self.line_style,
            "polarity": self.polarity,
            "waypoints": self.waypoints,
            "metadata": self.metadata,
        }

    @classmethod
    def from_orm(cls, orm_edge) -> "ModelEdge":
        return cls(
            id=str(orm_edge.id),
            project_id=str(orm_edge.project_id),
            source_node_id=str(orm_edge.source_node_id),
            target_node_id=str(orm_edge.target_node_id),
            edge_type=EdgeType(orm_edge.edge_type),
            line_style=orm_edge.line_style,
            polarity=orm_edge.polarity,
            waypoints=orm_edge.waypoints or [],
            metadata=orm_edge.metadata or {},
        )


@dataclass
class RunSpecs:
    start_time: float = 0
    stop_time: float = 365
    dt: float = 1.0
    time_units: str = "dias"
    n_runs_montecarlo: int = 1000
    integration_method: str = "euler"
    random_seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time,
            "stop_time": self.stop_time,
            "dt": self.dt,
            "time_units": self.time_units,
            "n_runs_montecarlo": self.n_runs_montecarlo,
            "integration_method": self.integration_method,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RunSpecs":
        return cls(
            start_time=data.get("start_time", 0),
            stop_time=data.get("stop_time", 365),
            dt=data.get("dt", 1.0),
            time_units=data.get("time_units", "dias"),
            n_runs_montecarlo=data.get("n_runs_montecarlo", 1000),
            integration_method=data.get("integration_method", "euler"),
            random_seed=data.get("random_seed"),
        )


@dataclass
class SimulationProject:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Nuevo Proyecto"
    description: str = ""
    domain: str = "dairy"
    run_specs: RunSpecs = field(default_factory=RunSpecs)
    nodes: List[ModelNode] = field(default_factory=list)
    edges: List[ModelEdge] = field(default_factory=list)
