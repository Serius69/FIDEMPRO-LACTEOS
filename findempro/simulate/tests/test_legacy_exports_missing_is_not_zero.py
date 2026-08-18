"""Las superficies legacy de export/API tampoco pueden inventar ceros.

Tres caminos heredados leían `variables` con `.get(clave, 0)`:

* el ranking de simulaciones (`simulate_result_view`), que puntuaba con 0 una
  corrida sin métricas y la mostraba como el peor negocio del conjunto;
* la comparación de simulaciones (`api_views`), donde una corrida sin datos
  entraba como un negocio que factura 0, nunca pierde —0 no es < 0— y competía
  por ser el "ganador";
* los escenarios de `api_v1_views`, que reportaban 0% de margen cuando el
  margen era en realidad indefinido (0/0).
"""
from types import SimpleNamespace

from simulate.views.api_views import _observed_series
from simulate.views.simulate_result_view import _observed_metric


def _rows(*variables):
    return [SimpleNamespace(variables=v, demand_mean=100.0) for v in variables]


# ── _observed_metric ────────────────────────────────────────────────────────
def test_metrica_ausente_es_none_no_cero():
    assert _observed_metric({}, 'NR') is None
    assert _observed_metric({'NR': None}, 'NR') is None


def test_metrica_cero_observada_se_respeta():
    """Un cero REALMENTE medido sigue siendo un cero."""
    assert _observed_metric({'NR': 0}, 'NR') == 0.0


def test_metrica_no_numerica_no_se_cuela_como_cero():
    assert _observed_metric({'NR': 'n/d'}, 'NR') is None


def test_metrica_presente_se_convierte_a_float():
    assert _observed_metric({'NR': '0.25'}, 'NR') == 0.25


# ── _observed_series ────────────────────────────────────────────────────────
def test_serie_omite_periodos_sin_la_variable():
    rows = _rows({'GT': 10.0}, {}, {'GT': 20.0})

    assert _observed_series(rows, 'GT') == [10.0, 20.0]


def test_serie_sin_ninguna_observacion_queda_vacia_no_en_ceros():
    rows = _rows({'_financial_status': 'incomplete'}, {})

    assert _observed_series(rows, 'GT') == []


def test_serie_conserva_las_perdidas_reales():
    """Las pérdidas observadas no se filtran: sólo se filtra lo ausente."""
    rows = _rows({'GT': -50.0}, {}, {'GT': 0.0})

    assert _observed_series(rows, 'GT') == [-50.0, 0.0]


def test_serie_tolera_filas_sin_atributo_variables():
    rows = [SimpleNamespace(demand_mean=1.0), SimpleNamespace(variables=None)]

    assert _observed_series(rows, 'GT') == []


def test_serie_ignora_valores_no_numericos():
    rows = _rows({'GT': 'error'}, {'GT': 5.0})

    assert _observed_series(rows, 'GT') == [5.0]


# ── Probabilidad de pérdida: el efecto que motivaba todo esto ───────────────
def test_probabilidad_de_perdida_no_se_diluye_con_ceros_inventados():
    """Con relleno de ceros, 2 pérdidas en 4 períodos observados parecían 2 de 6."""
    import numpy as np

    rows = _rows({'GT': -10.0}, {'GT': -20.0}, {'GT': 30.0}, {'GT': 40.0}, {}, {})

    serie = _observed_series(rows, 'GT')
    prob_perdida = float(np.mean(np.array(serie) < 0)) * 100

    assert len(serie) == 4
    assert prob_perdida == 50.0
