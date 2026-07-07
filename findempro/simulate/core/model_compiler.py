"""
ModelCompiler: Traduce el grafo visual (nodos + ecuaciones) al motor de simulación.
Conecta con los motores Monte Carlo y DES ya existentes en FindemproAI.
"""
import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelCompilerError(Exception):
    pass


class ModelCompiler:
    """
    Compila un grafo visual de nodos/edges a una configuración de simulación
    compatible con los motores existentes (monte_carlo.py, discrete_engine.py).

    Uso:
        compiler = ModelCompiler(nodes, edges, run_specs)
        config = compiler.compile()
        mc_config = compiler.compile_to_montecarlo_config()
    """

    def __init__(self, nodes: List[Dict], edges: List[Dict], run_specs: Dict):
        self.nodes = {n["id"]: n for n in nodes}
        self.edges = edges
        self.run_specs = run_specs
        self.compiled_model: Optional[Dict] = None

    # ─── VALIDACIÓN ──────────────────────────────────────────────────────────

    def validate(self) -> List[str]:
        """
        Valida el grafo antes de compilar.
        Retorna lista de errores. Lista vacía = modelo válido.
        """
        errors: List[str] = []

        for edge in self.edges:
            if edge.get("edge_type") == "flow":
                source = self.nodes.get(edge["source_node_id"], {})
                target = self.nodes.get(edge["target_node_id"], {})
                if source.get("node_type") not in ("stock", "flow"):
                    errors.append(
                        f"Flow '{edge['id']}': fuente debe ser stock o flow, "
                        f"es '{source.get('node_type')}'"
                    )
                if target.get("node_type") not in ("stock", "flow"):
                    errors.append(
                        f"Flow '{edge['id']}': destino debe ser stock o flow, "
                        f"es '{target.get('node_type')}'"
                    )

        for node_id, node in self.nodes.items():
            if node["node_type"] == "stock" and node.get("initial_value") is None:
                errors.append(f"Stock '{node['label']}': falta valor inicial")

        try:
            self._topological_sort()
        except ModelCompilerError as exc:
            errors.append(f"Dependencias circulares detectadas: {exc}")

        for node_id, node in self.nodes.items():
            if node["node_type"] in ("flow", "converter") and not node.get("equation"):
                errors.append(f"Nodo '{node['label']}': falta ecuación")

        return errors

    # ─── ORDENAMIENTO TOPOLÓGICO ──────────────────────────────────────────────

    def _topological_sort(self) -> List[str]:
        """
        Ordena nodos para evaluación correcta (DAG).
        Los stocks se evalúan usando valores del paso anterior (no forman ciclos).
        """
        graph: Dict[str, set] = defaultdict(set)
        in_degree: Dict[str, int] = defaultdict(int)

        for node_id in self.nodes:
            in_degree[node_id] = 0

        for edge in self.edges:
            if edge.get("edge_type") in ("causal", "info"):
                src = edge["source_node_id"]
                tgt = edge["target_node_id"]
                if src in self.nodes and tgt in self.nodes:
                    graph[src].add(tgt)
                    in_degree[tgt] += 1

        queue = deque(n for n in self.nodes if in_degree[n] == 0)
        sorted_nodes: List[str] = []

        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_nodes) != len(self.nodes):
            raise ModelCompilerError(
                "El modelo contiene dependencias circulares en converters/flows"
            )

        return sorted_nodes

    # ─── COMPILACIÓN PRINCIPAL ────────────────────────────────────────────────

    def compile(self) -> Dict[str, Any]:
        """
        Genera SimulationConfig compatible con el motor existente de FindemproAI.
        Lanza ModelCompilerError si el modelo es inválido.
        """
        errors = self.validate()
        if errors:
            raise ModelCompilerError(f"Modelo inválido: {'; '.join(errors)}")

        sorted_order = self._topological_sort()

        stocks = {nid: n for nid, n in self.nodes.items() if n["node_type"] == "stock"}
        flows = {nid: n for nid, n in self.nodes.items() if n["node_type"] == "flow"}
        converters = {nid: n for nid, n in self.nodes.items() if n["node_type"] == "converter"}

        # Mapear inflows/outflows por stock
        stock_flows: Dict[str, Dict] = defaultdict(lambda: {"inflows": [], "outflows": []})
        for edge in self.edges:
            if edge.get("edge_type") == "flow":
                src_id = edge["source_node_id"]
                tgt_id = edge["target_node_id"]
                src = self.nodes.get(src_id, {})
                tgt = self.nodes.get(tgt_id, {})
                if src.get("node_type") == "flow" and tgt.get("node_type") == "stock":
                    stock_flows[tgt_id]["inflows"].append(src_id)
                elif src.get("node_type") == "stock" and tgt.get("node_type") == "flow":
                    stock_flows[src_id]["outflows"].append(tgt_id)

        # Distribuciones para Monte Carlo
        distributions: Dict[str, Any] = {}
        for node in (*flows.values(), *converters.values()):
            if node.get("distribution_config"):
                distributions[node["label"]] = node["distribution_config"]

        self.compiled_model = {
            "type": "stock_and_flow",
            "run_specs": self.run_specs,
            "sorted_evaluation_order": sorted_order,
            "stocks": {
                nid: {
                    "label": n["label"],
                    "initial_value": n["initial_value"],
                    "units": n.get("units"),
                    "inflows": stock_flows[nid]["inflows"],
                    "outflows": stock_flows[nid]["outflows"],
                }
                for nid, n in stocks.items()
            },
            "flows": {
                nid: {
                    "label": n["label"],
                    "equation": n["equation"],
                    "units": n.get("units"),
                    "distribution": n.get("distribution_config"),
                }
                for nid, n in flows.items()
            },
            "converters": {
                nid: {
                    "label": n["label"],
                    "equation": n["equation"],
                    "units": n.get("units"),
                    "distribution": n.get("distribution_config"),
                }
                for nid, n in converters.items()
            },
            "distributions_for_montecarlo": distributions,
            "initial_state": {n["label"]: n["initial_value"] for n in stocks.values()},
        }

        logger.info(
            "Modelo compilado: %d stocks, %d flows, %d converters",
            len(stocks), len(flows), len(converters),
        )
        return self.compiled_model

    # ─── ADAPTADORES PARA MOTORES EXISTENTES ─────────────────────────────────

    def compile_to_montecarlo_config(self) -> Dict[str, Any]:
        """
        Convierte el modelo compilado al formato esperado por
        simulate/core/monte_carlo.py (MonteCarloConfig-compatible).
        """
        if not self.compiled_model:
            self.compile()

        start = self.run_specs.get("start_time", 0)
        stop = self.run_specs.get("stop_time", 365)
        dt = self.run_specs.get("dt", 1)

        mc_config: Dict[str, Any] = {
            "variables": {},
            "n_runs": self.run_specs.get("n_runs_montecarlo", 1000),
            "time_steps": int((stop - start) / dt),
            "dt": dt,
            "seed": self.run_specs.get("random_seed"),
            "stocks": self.compiled_model["stocks"],
            "flows": self.compiled_model["flows"],
            "converters": self.compiled_model["converters"],
        }

        # Mapear distribuciones al formato del motor existente
        _dist_map = {
            "normal": "normal",
            "lognormal": "lognormal",
            "triangular": "triangular",
            "uniform": "uniform",
            "gamma": "gamma",
            "beta": "beta",
            "weibull": "weibull",
        }

        for var_name, dist_config in self.compiled_model.get("distributions_for_montecarlo", {}).items():
            raw_type = dist_config.get("dist_type", "normal")
            mc_config["variables"][var_name] = {
                "distribution": _dist_map.get(raw_type, "normal"),
                "params": dist_config.get("params", {}),
            }

        return mc_config

    def compile_to_des_config(self) -> Dict[str, Any]:
        """
        Convierte el modelo compilado al formato esperado por
        simulate/core/discrete_engine.py (CompanyConfig-compatible).
        """
        if not self.compiled_model:
            self.compile()

        equations = {}
        initial_state = dict(self.compiled_model["initial_state"])

        for nid, node in self.compiled_model["flows"].items():
            if node["equation"]:
                equations[node["label"]] = node["equation"]

        for nid, node in self.compiled_model["converters"].items():
            if node["equation"]:
                equations[node["label"]] = node["equation"]

        return {
            "equations": equations,
            "initial_state": initial_state,
            "dt": self.run_specs.get("dt", 1),
            "time_steps": int(
                (self.run_specs.get("stop_time", 365) - self.run_specs.get("start_time", 0))
                / self.run_specs.get("dt", 1)
            ),
        }

    # ─── CAUSAL LOOP DIAGRAM ──────────────────────────────────────────────────

    def generate_causal_loop_diagram(self) -> Dict[str, Any]:
        """
        Genera datos para el Map View (CLD).
        Formato compatible con Cytoscape.js.
        """
        elements = []

        for nid, node in self.nodes.items():
            elements.append({
                "data": {
                    "id": nid,
                    "label": node["label"],
                    "type": node["node_type"],
                },
                "position": {
                    "x": node.get("position_x", 100),
                    "y": node.get("position_y", 100),
                },
                "classes": node["node_type"],
            })

        for edge in self.edges:
            elements.append({
                "data": {
                    "id": edge["id"],
                    "source": edge["source_node_id"],
                    "target": edge["target_node_id"],
                    "polarity": edge.get("polarity") or "",
                    "type": edge.get("edge_type", "causal"),
                },
                "classes": f"{edge.get('line_style', 'solid')} {edge.get('edge_type', 'causal')}",
            })

        return {
            "elements": elements,
            "style": self._get_cytoscape_style(),
        }

    def _get_cytoscape_style(self) -> List[Dict]:
        return [
            {
                "selector": "node.stock",
                "style": {
                    "shape": "rectangle",
                    "background-color": "#2563eb",
                    "color": "#fff",
                    "font-size": "11px",
                    "width": "100px",
                    "height": "50px",
                    "border-width": "3px",
                    "border-color": "#1d4ed8",
                },
            },
            {
                "selector": "node.flow",
                "style": {
                    "shape": "diamond",
                    "background-color": "#16a34a",
                    "color": "#fff",
                    "font-size": "10px",
                    "width": "60px",
                    "height": "60px",
                },
            },
            {
                "selector": "node.converter",
                "style": {
                    "shape": "ellipse",
                    "background-color": "#d97706",
                    "color": "#fff",
                    "font-size": "10px",
                    "width": "80px",
                    "height": "40px",
                },
            },
            {
                "selector": "edge",
                "style": {
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle",
                    "line-color": "#64748b",
                    "target-arrow-color": "#64748b",
                    "label": "data(polarity)",
                    "font-size": "14px",
                    "font-weight": "bold",
                    "color": "#ef4444",
                },
            },
            {
                "selector": "edge.dashed",
                "style": {"line-style": "dashed"},
            },
            {
                "selector": "edge.flow",
                "style": {"line-color": "#22c55e", "target-arrow-color": "#22c55e", "width": "2.5px"},
            },
        ]

    # ─── UTILIDADES ───────────────────────────────────────────────────────────

    def get_affected_variables(self, changed_var_labels: List[str]) -> List[str]:
        """
        Retorna lista de variables afectadas por un cambio en `changed_var_labels`.
        Útil para el live-update engine (re-evaluar solo el subgrafo afectado).
        """
        if not self.compiled_model:
            self.compile()

        label_to_id = {n["label"]: nid for nid, n in self.nodes.items()}
        affected_ids = set(label_to_id.get(lbl) for lbl in changed_var_labels if lbl in label_to_id)

        graph: Dict[str, set] = defaultdict(set)
        for edge in self.edges:
            graph[edge["source_node_id"]].add(edge["target_node_id"])

        visited = set()
        queue = deque(affected_ids)
        while queue:
            node_id = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)
            for neighbor in graph.get(node_id, set()):
                queue.append(neighbor)

        id_to_label = {nid: n["label"] for nid, n in self.nodes.items()}
        return [id_to_label[nid] for nid in visited if nid in id_to_label]
