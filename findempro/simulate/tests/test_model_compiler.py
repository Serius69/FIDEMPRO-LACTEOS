"""
test_model_compiler.py
======================
Tests unitarios para simulate/core/model_compiler.py.

Ejecutar con:
  cd findempro
  venv/Scripts/python.exe -m pytest simulate/tests/test_model_compiler.py -v --cov=simulate.core.model_compiler
"""

import pytest
from simulate.core.model_compiler import ModelCompiler, ModelCompilerError


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures de construcción
# ─────────────────────────────────────────────────────────────────────────────

def _make_stock(node_id: str, label: str, initial_value=100.0, **kwargs) -> dict:
    return {"id": node_id, "node_type": "stock", "label": label,
            "initial_value": initial_value, **kwargs}


def _make_flow(node_id: str, label: str, equation: str = "DE * 0.5", **kwargs) -> dict:
    return {"id": node_id, "node_type": "flow", "label": label,
            "equation": equation, **kwargs}


def _make_converter(node_id: str, label: str, equation: str = "100", **kwargs) -> dict:
    return {"id": node_id, "node_type": "converter", "label": label,
            "equation": equation, **kwargs}


def _edge(edge_id: str, src: str, tgt: str, edge_type: str = "causal", **kwargs) -> dict:
    return {"id": edge_id, "source_node_id": src, "target_node_id": tgt,
            "edge_type": edge_type, **kwargs}


DEFAULT_RUN_SPECS = {
    "start_time": 0,
    "stop_time": 30,
    "dt": 1,
    "n_runs_montecarlo": 500,
    "random_seed": 42,
}


@pytest.fixture
def minimal_compiler():
    """Modelo mínimo válido: 1 stock ← 1 flow (edge tipo 'flow')."""
    nodes = [
        _make_stock("s1", "Inventario", 1000.0),
        _make_flow("f1", "Entrada", "DE * 0.5"),
    ]
    edges = [_edge("e1", "f1", "s1", "flow")]
    return ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)


@pytest.fixture
def full_compiler():
    """Modelo con stock, flow, converter y aristas causales."""
    nodes = [
        _make_stock("s1", "Inventario", 500.0),
        _make_flow("f1", "Ventas", "DE * PVP"),
        _make_converter("c1", "PVP", "15.0"),
    ]
    edges = [
        _edge("e1", "f1", "s1", "flow"),
        _edge("e2", "c1", "f1", "causal"),
    ]
    return ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)


# ─────────────────────────────────────────────────────────────────────────────
# INIT y estructura básica
# ─────────────────────────────────────────────────────────────────────────────

class TestModelCompilerInit:

    def test_nodes_indexed_by_id(self, minimal_compiler):
        assert "s1" in minimal_compiler.nodes
        assert "f1" in minimal_compiler.nodes

    def test_edges_stored_as_list(self, minimal_compiler):
        assert isinstance(minimal_compiler.edges, list)
        assert len(minimal_compiler.edges) == 1

    def test_compiled_model_starts_none(self, minimal_compiler):
        assert minimal_compiler.compiled_model is None

    def test_empty_graph_no_crash(self):
        c = ModelCompiler([], [], DEFAULT_RUN_SPECS)
        assert c.nodes == {}
        assert c.edges == []


# ─────────────────────────────────────────────────────────────────────────────
# VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class TestModelCompilerValidation:

    def test_valid_model_returns_no_errors(self, minimal_compiler):
        errors = minimal_compiler.validate()
        assert errors == []

    def test_valid_full_model_returns_no_errors(self, full_compiler):
        errors = full_compiler.validate()
        assert errors == []

    def test_missing_stock_initial_value(self):
        nodes = [
            {"id": "s1", "node_type": "stock", "label": "Stock", "initial_value": None},
            _make_flow("f1", "Flow"),
        ]
        edges = [_edge("e1", "f1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        errors = c.validate()
        assert any("valor inicial" in e for e in errors)

    def test_missing_flow_equation(self):
        nodes = [
            _make_stock("s1", "Stock"),
            {"id": "f1", "node_type": "flow", "label": "FlowSinEq", "equation": None},
        ]
        edges = [_edge("e1", "f1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        errors = c.validate()
        assert any("ecuación" in e for e in errors)

    def test_missing_converter_equation(self):
        nodes = [
            _make_stock("s1", "Stock"),
            {"id": "c1", "node_type": "converter", "label": "Conv", "equation": ""},
        ]
        edges = []
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        errors = c.validate()
        assert any("ecuación" in e for e in errors)

    def test_invalid_flow_edge_source_is_converter(self):
        """Un 'flow' edge cuya fuente es converter → error de validación."""
        nodes = [
            _make_converter("c1", "Convertidor"),
            _make_stock("s1", "Stock"),
        ]
        edges = [_edge("e1", "c1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        errors = c.validate()
        assert any("fuente" in e for e in errors)

    def test_invalid_flow_edge_target_is_converter(self):
        """Un 'flow' edge cuyo destino es converter → error de validación."""
        nodes = [
            _make_flow("f1", "Flow"),
            _make_converter("c1", "Conv"),
        ]
        edges = [_edge("e1", "f1", "c1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        errors = c.validate()
        assert any("destino" in e for e in errors)

    def test_multiple_errors_accumulate(self):
        """validate() reporta todos los errores, no solo el primero."""
        nodes = [
            {"id": "s1", "node_type": "stock", "label": "S1", "initial_value": None},
            {"id": "f1", "node_type": "flow", "label": "F1", "equation": None},
        ]
        c = ModelCompiler(nodes, [], DEFAULT_RUN_SPECS)
        errors = c.validate()
        assert len(errors) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# ORDENAMIENTO TOPOLÓGICO
# ─────────────────────────────────────────────────────────────────────────────

class TestTopologicalSort:

    def test_valid_dag_returns_all_nodes(self, full_compiler):
        order = full_compiler._topological_sort()
        assert set(order) == {"s1", "f1", "c1"}

    def test_converter_before_dependent_flow(self, full_compiler):
        """c1 → f1 (causal): c1 debe aparecer antes que f1."""
        order = full_compiler._topological_sort()
        assert order.index("c1") < order.index("f1")

    def test_empty_graph_returns_empty(self):
        c = ModelCompiler([], [], DEFAULT_RUN_SPECS)
        assert c._topological_sort() == []

    def test_independent_nodes_all_present(self):
        nodes = [_make_converter("a", "A"), _make_converter("b", "B")]
        c = ModelCompiler(nodes, [], DEFAULT_RUN_SPECS)
        order = c._topological_sort()
        assert set(order) == {"a", "b"}

    def test_cycle_raises_model_compiler_error(self):
        """Ciclo entre converters → ModelCompilerError."""
        nodes = [
            _make_converter("c1", "A", "B * 2"),
            _make_converter("c2", "B", "A * 2"),
        ]
        edges = [
            _edge("e1", "c1", "c2", "causal"),
            _edge("e2", "c2", "c1", "causal"),
        ]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        with pytest.raises(ModelCompilerError, match="circular"):
            c._topological_sort()

    def test_cycle_detected_via_validate(self):
        """validate() reporta el ciclo como error de dependencia circular."""
        nodes = [
            _make_converter("c1", "A", "B * 2"),
            _make_converter("c2", "B", "A * 2"),
        ]
        edges = [
            _edge("e1", "c1", "c2", "causal"),
            _edge("e2", "c2", "c1", "causal"),
        ]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        errors = c.validate()
        assert any("circular" in e.lower() for e in errors)

    def test_three_node_chain_order(self):
        """A → B → C debe ordenarse [A, B, C]."""
        nodes = [
            _make_converter("a", "A", "10"),
            _make_converter("b", "B", "A * 2"),
            _make_converter("c", "C", "B + 1"),
        ]
        edges = [
            _edge("e1", "a", "b", "causal"),
            _edge("e2", "b", "c", "causal"),
        ]
        comp = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        order = comp._topological_sort()
        assert order.index("a") < order.index("b") < order.index("c")


# ─────────────────────────────────────────────────────────────────────────────
# COMPILACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class TestCompile:

    def test_compile_returns_dict(self, minimal_compiler):
        result = minimal_compiler.compile()
        assert isinstance(result, dict)

    def test_compile_sets_compiled_model(self, minimal_compiler):
        minimal_compiler.compile()
        assert minimal_compiler.compiled_model is not None

    def test_compile_structure_keys(self, minimal_compiler):
        result = minimal_compiler.compile()
        for key in ("type", "run_specs", "sorted_evaluation_order",
                    "stocks", "flows", "converters", "initial_state"):
            assert key in result

    def test_compile_type_is_stock_and_flow(self, minimal_compiler):
        result = minimal_compiler.compile()
        assert result["type"] == "stock_and_flow"

    def test_compile_counts(self, full_compiler):
        result = full_compiler.compile()
        assert len(result["stocks"]) == 1
        assert len(result["flows"]) == 1
        assert len(result["converters"]) == 1

    def test_compile_initial_state(self, minimal_compiler):
        result = minimal_compiler.compile()
        assert result["initial_state"]["Inventario"] == pytest.approx(1000.0)

    def test_compile_raises_on_invalid_model(self):
        nodes = [{"id": "s1", "node_type": "stock", "label": "S", "initial_value": None}]
        c = ModelCompiler(nodes, [], DEFAULT_RUN_SPECS)
        with pytest.raises(ModelCompilerError):
            c.compile()

    def test_compile_inflow_outflow_mapping(self):
        """Stock s1 recibe flow f1 como inflow."""
        nodes = [
            _make_stock("s1", "Stock"),
            _make_flow("f1", "Entrada"),
        ]
        edges = [_edge("e1", "f1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        result = c.compile()
        assert "f1" in result["stocks"]["s1"]["inflows"]

    def test_compile_outflow_mapping(self):
        """Stock s1 envía flow f1 como outflow."""
        nodes = [
            _make_stock("s1", "Stock"),
            _make_flow("f1", "Salida"),
        ]
        edges = [_edge("e1", "s1", "f1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        result = c.compile()
        assert "f1" in result["stocks"]["s1"]["outflows"]

    def test_compile_twice_idempotent(self, minimal_compiler):
        r1 = minimal_compiler.compile()
        r2 = minimal_compiler.compile()
        assert r1["type"] == r2["type"]
        assert set(r1["stocks"]) == set(r2["stocks"])

    def test_distributions_captured(self):
        """Flow con distribution_config queda en distributions_for_montecarlo."""
        dist_cfg = {"dist_type": "normal", "params": {"mean": 100, "std": 10}}
        nodes = [
            _make_stock("s1", "Stock"),
            _make_flow("f1", "Flow", distribution_config=dist_cfg),
        ]
        edges = [_edge("e1", "f1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        result = c.compile()
        assert "Flow" in result["distributions_for_montecarlo"]


# ─────────────────────────────────────────────────────────────────────────────
# compile_to_montecarlo_config()
# ─────────────────────────────────────────────────────────────────────────────

class TestCompileToMontecarloConfig:

    def test_returns_dict_with_required_keys(self, minimal_compiler):
        mc = minimal_compiler.compile_to_montecarlo_config()
        for key in ("variables", "n_runs", "time_steps", "dt", "seed", "stocks", "flows"):
            assert key in mc

    def test_time_steps_computed_correctly(self):
        """(stop - start) / dt = time_steps."""
        specs = {"start_time": 0, "stop_time": 60, "dt": 2, "n_runs_montecarlo": 200}
        nodes = [_make_stock("s1", "S")]
        c = ModelCompiler(nodes, [], specs)
        mc = c.compile_to_montecarlo_config()
        assert mc["time_steps"] == 30

    def test_n_runs_from_run_specs(self):
        specs = {**DEFAULT_RUN_SPECS, "n_runs_montecarlo": 999}
        nodes = [_make_stock("s1", "S")]
        c = ModelCompiler(nodes, [], specs)
        mc = c.compile_to_montecarlo_config()
        assert mc["n_runs"] == 999

    def test_seed_from_run_specs(self):
        specs = {**DEFAULT_RUN_SPECS, "random_seed": 123}
        nodes = [_make_stock("s1", "S")]
        c = ModelCompiler(nodes, [], specs)
        mc = c.compile_to_montecarlo_config()
        assert mc["seed"] == 123

    def test_distribution_mapping_normal(self):
        dist_cfg = {"dist_type": "normal", "params": {"mean": 500, "std": 50}}
        nodes = [
            _make_stock("s1", "S"),
            _make_flow("f1", "F", distribution_config=dist_cfg),
        ]
        edges = [_edge("e1", "f1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        mc = c.compile_to_montecarlo_config()
        assert mc["variables"]["F"]["distribution"] == "normal"

    def test_distribution_mapping_lognormal(self):
        dist_cfg = {"dist_type": "lognormal", "params": {"mean": 500, "std": 50}}
        nodes = [
            _make_stock("s1", "S"),
            _make_flow("f1", "F", distribution_config=dist_cfg),
        ]
        edges = [_edge("e1", "f1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        mc = c.compile_to_montecarlo_config()
        assert mc["variables"]["F"]["distribution"] == "lognormal"

    def test_unknown_distribution_falls_back_to_normal(self):
        dist_cfg = {"dist_type": "weibull_extreme", "params": {}}
        nodes = [
            _make_stock("s1", "S"),
            _make_flow("f1", "F", distribution_config=dist_cfg),
        ]
        edges = [_edge("e1", "f1", "s1", "flow")]
        c = ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)
        mc = c.compile_to_montecarlo_config()
        assert mc["variables"]["F"]["distribution"] == "normal"

    def test_triggers_compile_if_not_done(self):
        """compile_to_montecarlo_config() llama compile() automáticamente."""
        nodes = [_make_stock("s1", "S")]
        c = ModelCompiler(nodes, [], DEFAULT_RUN_SPECS)
        assert c.compiled_model is None
        mc = c.compile_to_montecarlo_config()
        assert mc is not None
        assert c.compiled_model is not None


# ─────────────────────────────────────────────────────────────────────────────
# compile_to_des_config()
# ─────────────────────────────────────────────────────────────────────────────

class TestCompileToDESConfig:

    def test_returns_required_keys(self, full_compiler):
        des = full_compiler.compile_to_des_config()
        for key in ("equations", "initial_state", "dt", "time_steps"):
            assert key in des

    def test_equations_from_flows(self, full_compiler):
        des = full_compiler.compile_to_des_config()
        assert "Ventas" in des["equations"]

    def test_equations_from_converters(self, full_compiler):
        des = full_compiler.compile_to_des_config()
        assert "PVP" in des["equations"]

    def test_initial_state_from_stocks(self, full_compiler):
        des = full_compiler.compile_to_des_config()
        assert des["initial_state"]["Inventario"] == pytest.approx(500.0)

    def test_dt_from_run_specs(self):
        specs = {**DEFAULT_RUN_SPECS, "dt": 0.25}
        nodes = [_make_stock("s1", "S")]
        c = ModelCompiler(nodes, [], specs)
        des = c.compile_to_des_config()
        assert des["dt"] == pytest.approx(0.25)


# ─────────────────────────────────────────────────────────────────────────────
# get_affected_variables() — subgrafo 5 nodos
# ─────────────────────────────────────────────────────────────────────────────

class TestGetAffectedVariables:
    """
    Grafo de 5 nodos:
      A → B → D
      A → C → E
    Cambiar A: afecta [A, B, C, D, E]
    Cambiar D: afecta solo [D]
    Cambiar B: afecta [B, D]
    """

    @pytest.fixture
    def five_node_compiler(self):
        nodes = [
            _make_converter("a", "A", "10"),
            _make_converter("b", "B", "A * 2"),
            _make_converter("c", "C", "A + 5"),
            _make_converter("d", "D", "B - 1"),
            _make_converter("e", "E", "C * 3"),
        ]
        edges = [
            _edge("e1", "a", "b", "causal"),
            _edge("e2", "a", "c", "causal"),
            _edge("e3", "b", "d", "causal"),
            _edge("e4", "c", "e", "causal"),
        ]
        return ModelCompiler(nodes, edges, DEFAULT_RUN_SPECS)

    def test_root_affects_all_five(self, five_node_compiler):
        five_node_compiler.compile()
        affected = five_node_compiler.get_affected_variables(["A"])
        assert set(affected) == {"A", "B", "C", "D", "E"}

    def test_leaf_affects_only_itself(self, five_node_compiler):
        five_node_compiler.compile()
        affected = five_node_compiler.get_affected_variables(["D"])
        assert set(affected) == {"D"}

    def test_mid_node_b_affects_b_and_d(self, five_node_compiler):
        five_node_compiler.compile()
        affected = five_node_compiler.get_affected_variables(["B"])
        assert set(affected) == {"B", "D"}

    def test_mid_node_c_affects_c_and_e(self, five_node_compiler):
        five_node_compiler.compile()
        affected = five_node_compiler.get_affected_variables(["C"])
        assert set(affected) == {"C", "E"}

    def test_unknown_label_returns_empty(self, five_node_compiler):
        five_node_compiler.compile()
        affected = five_node_compiler.get_affected_variables(["NoExiste"])
        assert affected == []

    def test_multiple_roots(self, five_node_compiler):
        five_node_compiler.compile()
        affected = five_node_compiler.get_affected_variables(["B", "C"])
        assert set(affected) == {"B", "C", "D", "E"}

    def test_triggers_compile_if_not_done(self, five_node_compiler):
        assert five_node_compiler.compiled_model is None
        affected = five_node_compiler.get_affected_variables(["A"])
        assert "A" in affected


# ─────────────────────────────────────────────────────────────────────────────
# generate_causal_loop_diagram()
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateCausalLoopDiagram:

    def test_returns_elements_and_style(self, full_compiler):
        full_compiler.compile()
        cld = full_compiler.generate_causal_loop_diagram()
        assert "elements" in cld
        assert "style" in cld

    def test_elements_count(self, full_compiler):
        full_compiler.compile()
        cld = full_compiler.generate_causal_loop_diagram()
        # 3 nodes + 2 edges
        assert len(cld["elements"]) == 5

    def test_node_element_has_data_and_position(self, full_compiler):
        full_compiler.compile()
        cld = full_compiler.generate_causal_loop_diagram()
        node_els = [e for e in cld["elements"] if "position" in e]
        assert len(node_els) == 3
        for el in node_els:
            assert "label" in el["data"]
            assert "type" in el["data"]

    def test_edge_element_has_source_target(self, full_compiler):
        full_compiler.compile()
        cld = full_compiler.generate_causal_loop_diagram()
        edge_els = [e for e in cld["elements"] if "position" not in e]
        assert len(edge_els) == 2
        for el in edge_els:
            assert "source" in el["data"]
            assert "target" in el["data"]

    def test_style_is_list(self, full_compiler):
        full_compiler.compile()
        cld = full_compiler.generate_causal_loop_diagram()
        assert isinstance(cld["style"], list)
        assert len(cld["style"]) > 0
