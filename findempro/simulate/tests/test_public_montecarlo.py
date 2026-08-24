"""El simulador público sin estado.

La ruta `/api/simulate/montecarlo/` la llamaba el onboarding anónimo desde el
primer día y no existía en el backend: devolvía 404 y el visitante leía "no
pudimos calcular tu proyección". Estas pruebas sujetan tanto el cálculo como el
límite de la superficie pública: cálculo sí, estado de cliente no.
"""
import json

import pytest
from django.urls import reverse

URL = '/api/simulate/montecarlo/'


def _post(client, **payload):
    return client.post(URL, data=json.dumps(payload), content_type='application/json')


def test_la_ruta_que_llama_el_onboarding_existe():
    assert reverse('api.public.montecarlo') == URL


@pytest.mark.django_db
def test_un_visitante_sin_cuenta_obtiene_su_proyeccion(client):
    r = _post(client, ventas_mes=10000, gastos_fijos=5000,
              tipo_negocio='comercio', horizonte=12, simulaciones=2000)
    assert r.status_code == 200, r.content
    d = r.json()
    for k in ('p5', 'p50', 'p95'):
        assert isinstance(d[k], (int, float)), f'{k} no es un número'
    # Los percentiles tienen que venir ordenados: si no, no son percentiles.
    assert d['p5'] <= d['p50'] <= d['p95']
    assert 0.0 <= d['probabilidad_perdida'] <= 1.0


@pytest.mark.django_db
def test_no_persiste_nada_del_visitante(client):
    """La superficie pública calcula; no guarda estado de cliente."""
    from simulate.models import Simulation

    antes = Simulation.objects.count()
    r = _post(client, ventas_mes=8000, gastos_fijos=3000, simulaciones=1000)
    assert r.status_code == 200
    assert r.json()['persistido'] is False
    assert Simulation.objects.count() == antes


@pytest.mark.django_db
def test_un_sector_desconocido_cae_al_generico_y_lo_declara(client):
    r = _post(client, ventas_mes=9000, gastos_fijos=4000,
              tipo_negocio='no-existe', simulaciones=1000)
    assert r.status_code == 200
    assert r.json()['sector_aplicado'] == 'generico'


@pytest.mark.django_db
@pytest.mark.parametrize('payload', [
    {'gastos_fijos': 5000},                                   # falta ventas_mes
    {'ventas_mes': 'muchas', 'gastos_fijos': 5000},           # no numérico
    {'ventas_mes': 'NaN', 'gastos_fijos': 5000},              # no finito
    {'ventas_mes': 10000, 'gastos_fijos': 5000, 'horizonte': 0},
    {'ventas_mes': 10000, 'gastos_fijos': 5000, 'simulaciones': 10 ** 9},
])
def test_entradas_invalidas_se_rechazan_con_400(client, payload):
    r = _post(client, **payload)
    assert r.status_code == 400, f'{payload} devolvió {r.status_code}'


@pytest.mark.django_db
def test_mas_gastos_fijos_nunca_mejora_la_utilidad(client):
    """Sujeta el sentido económico del cálculo, no solo su forma."""
    barato = _post(client, ventas_mes=10000, gastos_fijos=1000, simulaciones=4000).json()
    caro = _post(client, ventas_mes=10000, gastos_fijos=6000, simulaciones=4000).json()
    assert caro['p50'] < barato['p50']
