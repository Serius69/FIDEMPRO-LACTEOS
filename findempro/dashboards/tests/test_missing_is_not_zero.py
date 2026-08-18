"""El dashboard no puede convertir un fallo ni una ausencia en un veredicto.

Tres caminos presentaban lo que no se pudo calcular como si fuera un hecho
medido del negocio:

* el fallback de KPIs ante una excepción devolvía todo en 0, y `financial_health
  = 0` se mapeaba a estado `poor` — el usuario leía "el negocio necesita mejoras
  significativas" cuando lo que había ocurrido era un error interno;
* una recomendación sin métrica registrada tomaba `or 0.5` y se mostraba como
  "50%", una cifra que nadie midió (y que además pisaba un 0 legítimo);
* los ratios con denominador cero (sin ingresos, sin demanda, sin inventario)
  se reportaban como 0% en vez de indefinidos.

    ERROR != 0 · AUSENTE != 0 · DESCONOCIDO != SANO
"""
from dashboards.services.dashboard_service import DashboardService


class _Metrics:
    """BusinessMetrics mínimo para ejercitar los cálculos."""
    def __init__(self, **kw):
        self.revenue = kw.get('revenue', 0)
        self.costs = kw.get('costs', 0)
        self.profit = kw.get('profit', 0)
        self.profit_margin = kw.get('profit_margin', 0)
        self.roi = kw.get('roi', None)
        self.efficiency_score = kw.get('efficiency_score', 0)
        self.inventory = kw.get('inventory', 0)
        self.demand = kw.get('demand', 0)
        self.production = kw.get('production', 0)


# ── Ratios indefinidos ──────────────────────────────────────────────────────
def test_ratios_con_denominador_cero_son_no_disponibles():
    kpis = DashboardService._calculate_enhanced_kpis(_Metrics())

    assert kpis['cost_ratio'] is None          # sin ingresos
    assert kpis['revenue_per_product'] is None # sin inventario
    assert kpis['demand_fulfillment'] is None  # sin demanda


def test_ratios_con_denominador_valido_se_calculan():
    kpis = DashboardService._calculate_enhanced_kpis(
        _Metrics(revenue=1000, costs=400, inventory=10, demand=200, production=180)
    )

    assert kpis['cost_ratio'] == 40.0
    assert kpis['revenue_per_product'] == 100.0
    assert kpis['demand_fulfillment'] == 90.0


# ── Un error no es un veredicto ─────────────────────────────────────────────
def test_un_fallo_al_calcular_no_se_reporta_como_negocio_en_cero():
    # `None` en el objeto de métricas hace estallar las comparaciones internas.
    kpis = DashboardService._calculate_enhanced_kpis(object())

    assert kpis['financial_health'] is None
    assert kpis['net_profit'] is None
    assert kpis['efficiency_score'] is None


def test_sin_salud_financiera_el_resumen_no_dice_que_el_negocio_es_malo():
    resumen = DashboardService._generate_business_summary(
        _Metrics(), {'financial_health': None}
    )

    assert resumen['status'] == 'unknown'
    assert resumen['health_score'] is None
    assert 'necesita mejoras significativas' not in resumen['message']


def test_con_salud_financiera_el_resumen_sigue_calificando():
    resumen = DashboardService._generate_business_summary(
        _Metrics(), {'financial_health': 90}
    )

    assert resumen['status'] == 'excellent'
    assert resumen['health_score'] == 90.0


def test_salud_financiera_baja_sigue_reportandose_como_mala():
    """El arreglo no puede silenciar un diagnóstico negativo REAL."""
    resumen = DashboardService._generate_business_summary(
        _Metrics(), {'financial_health': 10}
    )

    assert resumen['status'] == 'poor'


# ── Scores sin factores ─────────────────────────────────────────────────────
def test_score_de_eficiencia_sin_factores_es_desconocido():
    assert DashboardService._calculate_efficiency_score(_Metrics()) is None


def test_score_de_rendimiento_sin_factores_no_es_cero():
    score = DashboardService._calculate_product_performance_score(object())

    assert score is None


# ── Dashboard vacío ─────────────────────────────────────────────────────────
def test_dashboard_vacio_no_publica_kpis_en_cero():
    vacio = DashboardService._get_empty_dashboard_data()

    assert vacio['summary']['status'] == 'no_data'
    assert vacio['summary']['health_score'] is None
    for clave, valor in vacio['business_kpis'].items():
        assert valor is None, f"{clave} se publicó como {valor!r} en un dashboard sin datos"
