"""
test_api_v1_wire_contract.py
============================
El contrato JSON que la SPA de ``/app/`` consume de la API v1.

Por qué existe este archivo
───────────────────────────
La suite de backend ejercitaba el MOTOR (`MonteCarloEngine`, `DemandModelService`)
y el ESTADO HTTP de las vistas, y la suite de frontend mockea `@/lib/api` entera
y renderiza contra un objeto escrito a mano. Nadie comprobaba que el cuerpo que
sale por el cable sea el cuerpo que la SPA lee: ambas suites podían estar en
verde con el producto roto.

Y lo estaba. `Simulate.tsx` hacía `result.time_series.periods.map(...)` y
`result.scenarios.pessimist.demand` sobre un `time_series` que es una LISTA de
períodos y un `scenarios` que es una LISTA de escenarios; `Forecast.tsx` hacía
`result.forecast.map(...)` sobre un `forecast` que es un OBJETO. Los tres son
`undefined.map` / propiedad de `undefined`: la página se cae en el render, sin
red de por medio, en cuanto la simulación devuelve 200.

Además la API tiraba dos números que el motor sí calcula:

  · `profit_median` — existe en `SimulationResult` desde 8edca05a3 («en una
    distribución asimétrica la media no es el escenario típico») pero
    `to_dict()` no lo emitía, así que sólo lo veía el simulador público y la
    SPA autenticada presentaba la media como el escenario esperado.
  · `rmse` — `DemandModelService` lo calcula y `ForecastAPIView` lo descartaba,
    dejando el pronóstico con un solo indicador de error (MAPE), que no está
    definido cuando alguna observación es cero.

Este archivo fija el contrato completo por endpoint. Si el servidor cambia de
forma, aquí se ve en rojo antes de que la SPA se caiga en producción.

Consumidores (mantener sincronizados con este archivo):
  frontend/src/types/index.ts        — SimulationResult, ForecastResult
  frontend/src/pages/Simulate.tsx    — render del Monte Carlo
  frontend/src/pages/Forecast.tsx    — render del pronóstico
  frontend/src/lib/api.ts            — runSimulation / runForecast / runFullPipeline
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient

# Payload equivalente al de `DEFAULTS` en `frontend/src/pages/Simulate.tsx`,
# reducido en iteraciones/períodos para que el test corra rápido. `random_seed`
# fijo: el contrato no puede depender del azar.
SIMULATE_PAYLOAD = {
    'demand_mean': 1000,
    'demand_std': 150,
    'unit_price': 25,
    'unit_cost': 12,
    'fixed_costs': 5000,
    'distribution_type': 'normal',
    'n_iterations': 1000,
    'time_periods': 4,
    'confidence_level': 0.95,
    'random_seed': 42,
}

# Equivalente a `SAMPLE_DATA` + defaults de `frontend/src/pages/Forecast.tsx`.
FORECAST_PAYLOAD = {
    'historical_data': [850, 920, 1050, 980, 1100, 1030, 1200, 1150, 1080, 1300, 1250, 1180],
    'periods': 3,
    'method': 'auto',
    'confidence_level': 0.95,
    'include_analysis': False,
}


@pytest.fixture
def api(db):
    client = APIClient()
    client.force_authenticate(
        User.objects.create_user(username='wire_contract_user', password='pw')
    )
    return client


def _assert_numbers(seccion, cuerpo, claves):
    """Cada clave existe y trae un número finito (no `null`, no ausente)."""
    for clave in claves:
        assert clave in cuerpo, f'{seccion}: falta la clave {clave!r}'
        valor = cuerpo[clave]
        assert isinstance(valor, (int, float)) and not isinstance(valor, bool), (
            f'{seccion}.{clave} debería ser numérico, llegó {valor!r}'
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /simulate/api/v1/simulate/
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def simulate_body(api):
    resp = api.post(
        reverse('simulate:api.v1.simulate'), data=SIMULATE_PAYLOAD, format='json'
    )
    assert resp.status_code == 200, resp.content
    return resp.json()


def test_simulate_expone_las_secciones_de_primer_nivel(simulate_body):
    assert set(simulate_body) >= {
        'demand', 'revenue', 'profit', 'risk', 'scenarios', 'time_series', 'metadata',
    }


def test_simulate_demand(simulate_body):
    _assert_numbers('demand', simulate_body['demand'],
                    ['mean', 'std', 'median', 'p5', 'p25', 'p75', 'p95',
                     'ci_lower', 'ci_upper'])


def test_simulate_revenue(simulate_body):
    _assert_numbers('revenue', simulate_body['revenue'], ['mean', 'std', 'p5', 'p95'])


def test_simulate_profit_incluye_la_mediana(simulate_body):
    """La mediana de utilidad tiene que salir por el cable, no sólo calcularse.

    `SimulationResult.profit_median` existe desde 8edca05a3 porque en una
    distribución asimétrica la media NO es el escenario típico. `to_dict()` la
    descartaba, así que la SPA autenticada sólo podía presentar la media —
    mientras el simulador público sí devolvía el p50. La misma pregunta recibía
    dos respuestas distintas según quién la hiciera.
    """
    profit = simulate_body['profit']
    _assert_numbers('profit', profit,
                    ['mean', 'std', 'median', 'p5', 'p95', 'var_95', 'cvar_95',
                     'ci_lower', 'ci_upper'])
    # La mediana es un estadístico del mismo lote, no un número suelto.
    assert profit['p5'] <= profit['median'] <= profit['p95']


def test_simulate_profit_no_fabrica_un_sharpe(simulate_body):
    """El beneficio monetario no es una serie de retornos periodizados."""
    profit = simulate_body['profit']
    assert profit['sharpe_ratio'] is None
    assert profit['ratio_basis'] == 'not_applicable_monetary_profit'
    assert profit['var_semantics'] == 'lower_profit_quantile'
    assert profit['cvar_semantics'] == 'lower_tail_mean_profit'


def test_simulate_risk(simulate_body):
    risk = simulate_body['risk']
    _assert_numbers('risk', risk,
                    ['probability_of_loss', 'probability_breakeven',
                     'confidence_level', 'var_confidence_level',
                     'cvar_confidence_level', 'value_at_risk_95',
                     'expected_shortfall'])
    assert risk['confidence_level'] == SIMULATE_PAYLOAD['confidence_level']


def test_simulate_scenarios_es_una_lista_de_escenarios_nombrados(simulate_body):
    """`scenarios` es una LISTA, no un objeto con claves fijas.

    `Simulate.tsx` leía `scenarios.pessimist.demand`: sobre una lista eso es
    `undefined.demand` y tumbaba el render.
    """
    scenarios = simulate_body['scenarios']
    assert isinstance(scenarios, list) and len(scenarios) == 5
    nombres = [s['name'] for s in scenarios]
    assert nombres == ['Pesimista', 'Conservador', 'Base', 'Optimista', 'Muy Optimista']
    for escenario in scenarios:
        _assert_numbers(f"scenarios[{escenario['name']}]", escenario,
                        ['demand_percentile', 'demand_value', 'revenue',
                         'total_costs', 'gross_profit', 'profit_margin_pct'])
    # Ordenados por demanda creciente: la SPA los pinta en ese orden.
    demandas = [s['demand_value'] for s in scenarios]
    assert demandas == sorted(demandas)


def test_simulate_time_series_es_una_lista_por_periodo(simulate_body):
    """`time_series` es una LISTA de períodos, no columnas paralelas.

    `Simulate.tsx` leía `time_series.periods.map(...)`: sobre una lista eso es
    `undefined.map` y tumbaba el render.
    """
    serie = simulate_body['time_series']
    assert isinstance(serie, list)
    assert len(serie) == SIMULATE_PAYLOAD['time_periods']
    assert [p['period'] for p in serie] == list(range(1, len(serie) + 1))
    for punto in serie:
        _assert_numbers(f"time_series[{punto['period']}]", punto,
                        ['period', 'seasonality_factor', 'demand_mean',
                         'demand_p5', 'demand_p95', 'revenue_mean',
                         'profit_mean', 'profit_p5', 'profit_p95'])


def test_simulate_metadata(simulate_body):
    metadata = simulate_body['metadata']
    assert metadata['n_iterations'] == SIMULATE_PAYLOAD['n_iterations']
    # `distribution_used`, no `distribution_type`: es la que el motor usó de
    # verdad, que puede no ser la pedida.
    assert metadata['distribution_used'] == SIMULATE_PAYLOAD['distribution_type']
    assert metadata['confidence_level'] == SIMULATE_PAYLOAD['confidence_level']


# ─────────────────────────────────────────────────────────────────────────────
# POST /simulate/api/v1/simulate/async/ → GET .../status/<task_id>/
# ─────────────────────────────────────────────────────────────────────────────

def test_async_devuelve_el_mismo_contrato_que_el_sincrono(api, simulate_body):
    """La SPA sólo usa la vía async: no puede tener otra forma que la síncrona."""
    encolar = api.post(
        reverse('simulate:api.v1.simulate_async'), data=SIMULATE_PAYLOAD, format='json'
    )
    assert encolar.status_code == 202, encolar.content

    estado = api.get(encolar.json()['status_url'])
    assert estado.status_code == 200, estado.content
    cuerpo = estado.json()
    assert cuerpo['state'] == 'SUCCESS', cuerpo

    resultado = cuerpo['result']
    assert set(resultado) == set(simulate_body), (
        'el resultado async no tiene las mismas secciones que el síncrono'
    )
    for seccion in ('demand', 'revenue', 'profit', 'risk', 'metadata'):
        assert set(resultado[seccion]) == set(simulate_body[seccion]), (
            f'async y síncrono difieren en las claves de {seccion}'
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /simulate/api/v1/forecast/
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def forecast_body(api):
    resp = api.post(
        reverse('simulate:api.v1.forecast'), data=FORECAST_PAYLOAD, format='json'
    )
    assert resp.status_code == 200, resp.content
    return resp.json()


def test_forecast_es_un_objeto_con_series_paralelas(forecast_body):
    """`forecast` es un OBJETO, no un array de valores.

    `Forecast.tsx` hacía `result.forecast.map(...)`: sobre un objeto eso es
    `forecast.map is not a function` y tumbaba el render.
    """
    forecast = forecast_body['forecast']
    assert isinstance(forecast, dict)

    n = FORECAST_PAYLOAD['periods']
    assert forecast['periods'] == n
    for clave in ('values', 'ci_lower', 'ci_upper'):
        serie = forecast[clave]
        assert isinstance(serie, list) and len(serie) == n, (
            f'forecast.{clave} debería traer {n} valores'
        )
        assert all(isinstance(v, (int, float)) for v in serie)

    # El intervalo envuelve a la proyección, punto a punto.
    for i in range(n):
        assert forecast['ci_lower'][i] <= forecast['values'][i] <= forecast['ci_upper'][i]

    assert forecast['method_used'] in (
        'linear', 'moving_average', 'exponential_smoothing',
    )
    assert forecast['confidence_level'] == FORECAST_PAYLOAD['confidence_level']


def test_forecast_expone_las_metricas_de_error_que_calcula(forecast_body):
    """RMSE viaja junto a MAPE en vez de no existir.

    `DemandForecast.rmse` estaba declarado y no se llenaba nunca, y la vista
    tampoco lo devolvía. Ahora se calcula sobre el MISMO holdout temporal que
    MAPE y sale por el cable.
    """
    forecast = forecast_body['forecast']
    assert forecast['mape'] > 0, 'forecast.mape ausente o vacío'
    assert forecast['rmse'] > 0, 'forecast.rmse ausente o vacío'


def test_forecast_da_error_medible_aunque_mape_no_este_definido(api):
    """El caso que motiva RMSE: demanda parada en cero en el tramo de holdout.

    MAPE es un error RELATIVO: contra observaciones en cero no está definido y
    el servicio devuelve None antes que inventarlo. Sin RMSE el pronóstico
    salía entonces sin ningún indicador de error, y la SPA no tenía nada que
    mostrar sobre su calidad.
    """
    resp = api.post(
        reverse('simulate:api.v1.forecast'),
        data={**FORECAST_PAYLOAD,
              # 12 puntos; el holdout es el último 20% → los dos ceros finales.
              'historical_data': [40, 35, 30, 28, 25, 20, 18, 12, 8, 4, 0, 0]},
        format='json',
    )
    assert resp.status_code == 200, resp.content
    forecast = resp.json()['forecast']

    assert forecast['mape'] is None, 'MAPE no puede definirse contra ceros'
    assert forecast['rmse'] is not None and forecast['rmse'] >= 0, (
        'sin MAPE, RMSE es el único indicador de error que queda'
    )


def test_forecast_simulation_params_encadena_con_simulate(forecast_body):
    """`simulation_params` alimenta el endpoint de simulación: mismos nombres."""
    params = forecast_body['simulation_params']
    _assert_numbers('simulation_params', params, ['demand_mean', 'demand_std'])
    assert params['distribution_type'] in (
        'normal', 'lognormal', 'gamma', 'uniform', 'exponential',
    )


def test_forecast_sin_analisis_no_incluye_la_seccion_analysis(forecast_body):
    """`include_analysis: false` significa que no viene, no que viene vacía."""
    assert 'analysis' not in forecast_body
