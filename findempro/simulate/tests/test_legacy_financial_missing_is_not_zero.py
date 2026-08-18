"""Un dato financiero ausente no es un cero observado.

`ResultSimulation.variables` es un JSON: una corrida vieja, parcial o fallida
puede no traer `IT`/`GT`/`TG`. El analizador legacy convertía esas ausencias en
`0.0` y a partir de ahí construía totales, márgenes, "mejor día" y hasta un
estado de salud del negocio. El resultado era que **la falta de datos se
presentaba como un negocio que factura Bs 0.00 y pierde todos los días**, o
peor, como uno estable — porque una serie de ceros tiene volatilidad cero y eso
sumaba puntos de salud.

Reglas que fijan estos tests:
    AUSENTE  != 0
    INDEFINIDO != 0
    DESCONOCIDO != SANO
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from simulate.utils.simulation_financial_utils import SimulationFinancialAnalyzer


def _results(variables_por_dia):
    """Construye resultados con la forma mínima que consume el analizador."""
    base = date(2026, 1, 1)
    return [
        SimpleNamespace(variables=v, date=base + timedelta(days=i), demand_mean=100.0)
        for i, v in enumerate(variables_por_dia)
    ]


# Una corrida parcial/fallida: `variables` trae algo (si viniera vacío del todo el
# analizador descarta la fila), pero ninguna de las claves financieras.
SIN_FINANZAS = {'_financial_status': 'incomplete', 'DPH': 100.0}

COMPLETO = {'IT': 1000.0, 'GT': 200.0, 'TG': 800.0, 'GO': 500.0, 'GG': 100.0,
            'CTAI': 150.0, 'CTTL': 30.0, 'CA': 10.0, 'CTM': 10.0,
            'TPV': 50.0, 'PVP': 20.0, 'PED': 40.0,
            'IB': 300.0, 'MB': 0.3, 'NR': 0.2, 'RI': 0.25}


# ─────────────────────────────────────────────────────────────
# Extracción: ausente → None, nunca 0.0
# ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize('campo', [
    'revenue', 'expected_revenue', 'operating_costs', 'general_expenses',
    'total_costs', 'material_costs', 'transport_costs', 'storage_costs',
    'wastage_costs', 'net_profit', 'break_even', 'sales_volume', 'price',
])
def test_campo_monetario_ausente_no_se_convierte_en_cero(campo):
    analyzer = SimulationFinancialAnalyzer()

    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS]))

    assert diario[0][campo] is None, (
        f"{campo} ausente se reportó como {diario[0][campo]!r} en vez de None"
    )


def test_campo_monetario_presente_se_respeta():
    analyzer = SimulationFinancialAnalyzer()

    diario = analyzer._extract_daily_financials(_results([COMPLETO]))

    assert diario[0]['revenue'] == 1000.0
    assert diario[0]['net_profit'] == 200.0
    assert diario[0]['total_costs'] == 800.0


# ─────────────────────────────────────────────────────────────
# Agregación: sin observaciones → None, no 0
# ─────────────────────────────────────────────────────────────
def test_totales_sin_ninguna_observacion_son_no_disponibles():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 3))

    rent = analyzer._analyze_profitability(diario)
    kpis = analyzer._calculate_financial_kpis(diario)

    assert rent['total_revenue'] is None
    assert rent['total_profit'] is None
    assert kpis['total_revenue'] is None
    assert kpis['total_profit'] is None
    assert kpis['total_costs'] is None


def test_dias_rentables_no_se_cuentan_sobre_datos_ausentes():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 3))

    rent = analyzer._analyze_profitability(diario)

    # Sin utilidades observadas no hay días con pérdida: no se observó nada.
    assert rent['loss_days'] == 0
    assert rent['profitable_days'] == 0
    assert rent['profitability_rate'] is None
    assert rent['observed_days'] == 0


def test_margen_indefinido_sin_ingresos_no_es_cero_por_ciento():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS]))

    kpis = analyzer._calculate_financial_kpis(diario)

    assert kpis['profit_margin'] is None


def test_volatilidad_sin_observaciones_es_no_disponible():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 2))

    rent = analyzer._analyze_profitability(diario)

    assert rent['profit_volatility'] is None


def test_mejor_y_peor_dia_no_existen_sin_utilidades_observadas():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 2))

    kpis = analyzer._calculate_financial_kpis(diario)

    assert kpis['best_day_profit'] is None
    assert kpis['best_day_number'] is None
    assert kpis['worst_day_profit'] is None
    assert kpis['worst_day_number'] is None


# ─────────────────────────────────────────────────────────────
# Agregación parcial: se agrega lo observado y se declara la cobertura
# ─────────────────────────────────────────────────────────────
def test_agregacion_parcial_usa_solo_lo_observado_y_declara_cobertura():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([COMPLETO, SIN_FINANZAS]))

    rent = analyzer._analyze_profitability(diario)

    assert rent['total_revenue'] == 1000.0     # no 1000/2 ni 1000+0
    assert rent['observed_days'] == 1
    assert rent['total_days'] == 2
    assert rent['profitable_days'] == 1
    assert rent['loss_days'] == 0
    assert rent['profitability_rate'] == 1.0   # 1 de 1 observado, no 1 de 2


# ─────────────────────────────────────────────────────────────
# Salud del negocio: desconocido != sano
# ─────────────────────────────────────────────────────────────
def test_salud_del_negocio_es_desconocida_sin_datos_financieros():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 3))

    kpis = analyzer._calculate_financial_kpis(diario)
    rent = analyzer._analyze_profitability(diario)
    salud = analyzer._determine_business_health(
        kpis, rent, {'overall_risk': 'unknown', 'risk_factors': []}
    )

    assert salud == 'unknown', (
        f"sin ningún dato financiero el negocio se calificó como {salud!r}"
    )


def test_la_ausencia_de_datos_no_suma_puntos_por_estabilidad():
    """Una serie de ceros inventados tiene volatilidad 0 y parecía estable."""
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 3))

    rent = analyzer._analyze_profitability(diario)
    salud = analyzer._determine_business_health(
        kpis={}, profitability=rent, risk_assessment={'overall_risk': 'low'}
    )

    assert salud == 'unknown'


def test_salud_del_negocio_se_calcula_normalmente_con_datos():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([COMPLETO] * 3))

    kpis = analyzer._calculate_financial_kpis(diario)
    rent = analyzer._analyze_profitability(diario)
    salud = analyzer._determine_business_health(
        kpis, rent, {'overall_risk': 'low', 'risk_factors': []}
    )

    assert salud in {'excellent', 'good', 'fair', 'poor'}
    assert salud != 'unknown'


# ─────────────────────────────────────────────────────────────
# Costos y eficiencia
# ─────────────────────────────────────────────────────────────
def test_estructura_de_costos_sin_observaciones_es_no_disponible():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 2))

    costos = analyzer._analyze_costs(diario)

    assert costos['total_costs'] is None
    assert costos['average_daily_cost'] is None
    assert costos['cost_structure']['operating'] is None
    assert costos['cost_per_unit']['average'] is None


def test_eficiencia_sin_observaciones_es_no_disponible():
    analyzer = SimulationFinancialAnalyzer()
    diario = analyzer._extract_daily_financials(_results([SIN_FINANZAS] * 2))

    ef = analyzer._analyze_efficiency(diario)

    assert ef['revenue_per_unit']['average'] is None
    assert ef['cost_per_unit']['average'] is None
    assert ef['contribution_margin']['per_unit'] is None
