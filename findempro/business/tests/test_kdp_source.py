"""Findempro siembra simulaciones con estos números: no pueden ser inventados."""
from unittest.mock import Mock, patch

import pytest

from business import kdp_source


def _mock(payload):
    return patch("business.kdp_source.requests.get",
                 return_value=Mock(json=lambda: payload, raise_for_status=Mock()))


def _fx(**over):
    p = {"observed_at": "2026-08-24T00:00:00+00:00", "value": 11.5,
         "unit": "BOB_per_unit", "currency": "BOB", "source_slug": "dolarapi-bo",
         "quality": "ok", "provenance": "observed"}
    p.update(over)
    return p


def test_oficial_observado_llega_completo():
    with _mock(_fx()):
        v, src = kdp_source.fetch_fx_oficial()
    assert v == 11.5
    assert src.startswith("kdp:")


def test_oficial_rechaza_provenance_no_observada():
    with _mock(_fx(provenance="fallback")):
        with pytest.raises(kdp_source.KdpUnavailable, match="provenance"):
            kdp_source.fetch_fx_oficial()


def test_oficial_rechaza_fila_rechazada():
    with _mock(_fx(quality="rejected")):
        with pytest.raises(kdp_source.KdpUnavailable, match="rechazado"):
            kdp_source.fetch_fx_oficial()


def test_la_banda_no_ancla_el_valor_historico():
    """El bug original era una banda 6,5–7,5. La nueva debe aceptar 11,50."""
    with _mock(_fx(value=11.5)):
        v, _ = kdp_source.fetch_fx_oficial()
    assert v == 11.5
    with _mock(_fx(value=20.0)):
        v, _ = kdp_source.fetch_fx_oficial()
    assert v == 20.0


def test_oficial_fuera_de_banda_se_rechaza():
    with _mock(_fx(value=0.0)):
        with pytest.raises(kdp_source.KdpUnavailable, match="fuera de banda"):
            kdp_source.fetch_fx_oficial()


def _infl(**over):
    p = {"series": "inflacion_doce_meses", "provenance": "observed",
         "unit": "percent",
         "observations": [{"fecha": "2026-06-30", "valor": 9.23,
                           "source": "bcb-semanal-bulk", "quality": "ok"},
                          {"fecha": "2026-07-31", "valor": 4.93,
                           "source": "bcb-semanal-bulk", "quality": "ok"}]}
    p.update(over)
    return p


def test_inflacion_toma_la_ultima_observacion():
    with _mock(_infl()):
        v, src = kdp_source.fetch_inflacion_anual()
    assert v == 4.93
    assert src.startswith("kdp:")


def test_inflacion_rechaza_serie_construida():
    with _mock(_infl(provenance="constructed")):
        with pytest.raises(kdp_source.KdpUnavailable, match="provenance"):
            kdp_source.fetch_inflacion_anual()


def test_inflacion_rechaza_serie_vacia():
    with _mock(_infl(observations=[])):
        with pytest.raises(kdp_source.KdpUnavailable, match="observaciones"):
            kdp_source.fetch_inflacion_anual()


def test_kdp_caido_no_inventa():
    import requests
    with patch("business.kdp_source.requests.get",
               side_effect=requests.RequestException("boom")):
        with pytest.raises(kdp_source.KdpUnavailable):
            kdp_source.fetch_fx_oficial()
