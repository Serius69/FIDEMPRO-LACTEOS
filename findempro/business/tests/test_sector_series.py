"""
Tests de los perfiles estacionales por sector (business.data.bolivia_sector_series),
el comando ingest_ine_series y su cableado en el generador de demanda.
"""
import json
import statistics
from io import StringIO

import pytest
from django.core.management import call_command

from business.data import bolivia_sector_series as ss
from business.services.seed_service import generate_answers, ProductBaseline


# ─────────────────────────────────────────────────────────────────────────────
# Perfiles
# ─────────────────────────────────────────────────────────────────────────────
def test_profiles_cover_19_types_normalized():
    assert set(ss.BUSINESS_TYPE_SEASONALITY) == set(range(1, 20))
    for bt, f in ss.BUSINESS_TYPE_SEASONALITY.items():
        assert len(f) == 12, f"tipo {bt} sin 12 meses"
        assert abs(sum(f) / 12 - 1.0) < 0.005, f"tipo {bt} no está normalizado a media 1.0"
        assert all(x > 0 for x in f)


def test_monthly_factor_bounds_and_flat_fallback():
    assert ss.monthly_factor(10, 0) == 1.0       # mes inválido
    assert ss.monthly_factor(10, 13) == 1.0
    assert ss.monthly_factor(999, 6) == 1.0      # tipo desconocido → plano
    assert ss.seasonal_factors(999) == [1.0] * 12


def test_known_bolivian_seasonality_peaks():
    """Los picos deben caer donde manda la estacionalidad boliviana real."""
    # Retail (10): pico diciembre (aguinaldo).
    assert 12 in ss.peak_months(10)
    # Panadería (4): pico noviembre (Todos Santos).
    assert 11 in ss.peak_months(4)
    # Educación (14): pico febrero (inicio escolar), NO diciembre.
    assert 2 in ss.peak_months(14) and 12 not in ss.peak_months(14)
    # Agricultura (2): pico en cosecha (abr-jul), NO diciembre.
    assert any(m in ss.peak_months(2) for m in (4, 5, 6, 7))
    assert 12 not in ss.peak_months(2)
    # Construcción (18): pico estación seca (ago-oct), NO temporada de lluvias.
    assert any(m in ss.peak_months(18) for m in (8, 9, 10))
    assert 1 not in ss.peak_months(18)


# ─────────────────────────────────────────────────────────────────────────────
# Cableado en el generador de demanda
# ─────────────────────────────────────────────────────────────────────────────
def _baseline():
    return ProductBaseline(
        name="X", unit="kg", price=10, unit_cost=6, daily_demand=1000, daily_clients=50,
        employees=5, monthly_salaries=15000, daily_fixed_cost=300, transport_unit_cost=0.2,
        marketing_monthly=800, demand_cv=0.05)


def _corr(a, b):
    n = len(a); ma = sum(a) / n; mb = sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db)


@pytest.mark.parametrize("bt", [2, 4, 10, 14, 18])
def test_generated_demand_follows_real_profile(bt):
    """La demanda generada con business_type debe seguir el perfil real del sector."""
    ans = generate_answers(_baseline(), n_history=360, business_type=bt)
    monthly = [statistics.mean(ans["DH"][m * 30:(m + 1) * 30]) for m in range(12)]
    assert _corr(monthly, ss.seasonal_factors(bt)) > 0.9


def test_without_business_type_is_legacy():
    """Sin business_type se conserva el comportamiento previo (no rompe compatibilidad)."""
    ans = generate_answers(_baseline(), n_history=40)
    assert len(ans["DH"]) == 40
    assert all(v >= 0 for v in ans["DH"])


# ─────────────────────────────────────────────────────────────────────────────
# Mezcla perfil del sector × meses pico del producto
# ─────────────────────────────────────────────────────────────────────────────
def test_blended_profile_lifts_product_peaks_over_sector():
    """
    Un producto con peak_months propios (que difieren del perfil del tipo) debe
    quedar POR ENCIMA del perfil del sector solo en esos meses, y renormalizado
    a media 1.0. Caso: Tour Turístico (tipo 16 = hotelería, pico Carnaval/dic)
    con temporada alta real jun-ago.
    """
    from business.services.seed_service import _blended_seasonal_profile

    bt = 16
    peaks = (6, 7, 8)
    sector = ss.seasonal_factors(bt)
    blended = _blended_seasonal_profile(bt, peaks)

    assert len(blended) == 12
    assert abs(sum(blended) / 12 - 1.0) < 0.01                 # media ≈ 1.0
    for m in peaks:
        assert blended[m - 1] > sector[m - 1], f"mes {m} no quedó realzado"
    # Sin peak_months propios, el perfil es exactamente el del sector.
    assert _blended_seasonal_profile(bt, ()) == tuple(sector)


def test_blended_profile_preserves_sector_correlation():
    """El realce es modesto: la demanda con picos propios sigue correlacionando
    fuerte con el perfil del sector (no lo destruye)."""
    baseline = ProductBaseline(
        name="TourTest", unit="servicios", price=320, unit_cost=190,
        daily_demand=9, daily_clients=9, employees=4, monthly_salaries=12200,
        daily_fixed_cost=220, transport_unit_cost=15.0, marketing_monthly=1800,
        demand_cv=0.02, seasonal=True, peak_months=[6, 7, 8])
    ans = generate_answers(baseline, n_history=360, business_type=16)
    monthly = [statistics.mean(ans["DH"][m * 30:(m + 1) * 30]) for m in range(12)]
    assert _corr(monthly, ss.seasonal_factors(16)) > 0.6      # sigue el sector
    # jun-ago por encima del promedio anual (temporada alta propia visible).
    annual_mean = statistics.mean(monthly)
    assert statistics.mean(monthly[5:8]) > annual_mean


# ─────────────────────────────────────────────────────────────────────────────
# Comando ingest_ine_series
# ─────────────────────────────────────────────────────────────────────────────
def test_ingest_offline_writes_valid_json(tmp_path, monkeypatch):
    out_file = tmp_path / "bolivia_sector_series.json"
    monkeypatch.setattr(
        "business.management.commands.ingest_ine_series.OUTPUT_PATH", out_file)

    stdout = StringIO()
    call_command("ingest_ine_series", "--offline", stdout=stdout)

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(data["sectors"]) == 19
    assert data["live_signal"]["ine_reachable"] is False        # offline
    s10 = data["sectors"]["10"]
    assert len(s10["monthly_factors"]) == 12
    assert 12 in s10["peak_months"]                              # retail: dic


def test_ingest_dry_run_writes_nothing(tmp_path, monkeypatch):
    out_file = tmp_path / "no.json"
    monkeypatch.setattr(
        "business.management.commands.ingest_ine_series.OUTPUT_PATH", out_file)
    call_command("ingest_ine_series", "--offline", "--dry-run", stdout=StringIO())
    assert not out_file.exists()


# ─────────────────────────────────────────────────────────────────────────────
# Parseo de la nota de prensa del IPC (INE WP REST) — offline, con fixture real
# ─────────────────────────────────────────────────────────────────────────────
# Texto real de la nota del IPC de junio 2026 (INE, WP REST), con shortcodes vc_.
_IPC_NOTE_JUNIO_2026 = (
    "[vc_row][vc_column][vc_column_text] La Paz, 3 de julio de 2026 (INE). – El "
    "Índice de Precios al Consumidor (IPC) registró una variación mensual positiva "
    "de 2,15% en junio de 2026, con relación a mayo del mismo año. Con este "
    "resultado, la inflación acumulada durante el primer semestre de 2026 alcanzó a "
    "4,82%, mientras que la variación a doce meses se situó en 9,23%. "
    "Comportamiento de los precios al consumidor, según regiones La variación "
    "mensual positiva de 2,15% se explica por: Las mayores variaciones se "
    "registraron en Oruro 3,86%; Región Metropolitana Kanata 3,65; Conurbación La "
    "Paz 3,40%; Potosí 3,08%; Sucre 2,57%; Cobija 1,08%; Trinidad 0,93% y Tarija "
    "0,37%. [/vc_column_text][/vc_column][/vc_row]"
)
_IPC_TITLE_JUNIO = ("Bolivia alcanzó una variación positiva de 2,15% en el Índice "
                    "de Precios al Consumidor en junio de 2026")


def test_parse_ipc_note_extracts_levels():
    from business.management.commands.ingest_ine_series import Command
    ipc = Command._parse_ipc_note(
        _IPC_TITLE_JUNIO, _IPC_NOTE_JUNIO_2026, "2026-07-03", "https://x")
    assert ipc["monthly_pct"] == 2.15
    assert ipc["annual_pct"] == 9.23           # a doce meses
    assert ipc["accumulated_pct"] == 4.82
    assert ipc["period"] == "junio de 2026"
    assert ipc["source"] == "ine-wp-rest"


def test_parse_ipc_note_extracts_regional():
    from business.management.commands.ingest_ine_series import Command
    ipc = Command._parse_ipc_note(
        _IPC_TITLE_JUNIO, _IPC_NOTE_JUNIO_2026, "2026-07-03", "https://x")
    reg = ipc["regional"]
    assert reg["Oruro"] == 3.86
    assert reg["Potosí"] == 3.08
    assert reg["Tarija"] == 0.37
    assert 6 <= len(reg) <= 10                  # ~8 ciudades, sin basura


def test_parse_ipc_note_degrades_gracefully():
    """Un texto sin cifras no revienta: devuelve None en los niveles."""
    from business.management.commands.ingest_ine_series import Command
    ipc = Command._parse_ipc_note("Nota sin datos", "<p>sin cifras aquí</p>",
                                  "2026-01-01", "https://x")
    assert ipc["monthly_pct"] is None
    assert ipc["regional"] is None


# ─────────────────────────────────────────────────────────────────────────────
# Señal IPC persistida → helpers de consumo (live_ipc / regional_price_pressure)
# ─────────────────────────────────────────────────────────────────────────────
def _write_signal_json(tmp_path, ipc):
    p = tmp_path / "bolivia_sector_series.json"
    p.write_text(json.dumps({"live_signal": {"ipc": ipc}}), encoding="utf-8")
    return p


def test_regional_price_pressure_normalized(tmp_path, monkeypatch):
    p = _write_signal_json(tmp_path, {
        "period": "junio de 2026", "annual_pct": 9.23,
        "regional": {"Oruro": 3.86, "Potosí": 3.08, "Tarija": 0.37}})
    monkeypatch.setattr(ss, "_JSON_PATH", p)

    assert ss.live_ipc()["annual_pct"] == 9.23
    rp = ss.regional_price_pressure()
    assert abs(sum(rp.values()) / len(rp) - 1.0) < 1e-3   # media ≈ 1.0 (redondeo 4 dec.)
    assert rp["Oruro"] > 1.0 > rp["Tarija"]               # caro vs barato
    assert rp["Oruro"] == round(1 + (3.86 - (3.86 + 3.08 + 0.37) / 3) / 100, 4)


def test_regional_price_pressure_none_without_signal(tmp_path, monkeypatch):
    # Sin archivo → None (best-effort, no revienta).
    monkeypatch.setattr(ss, "_JSON_PATH", tmp_path / "no-existe.json")
    assert ss.live_ipc() is None
    assert ss.regional_price_pressure() is None
    # Con archivo pero refresco offline (ipc null) → None.
    monkeypatch.setattr(ss, "_JSON_PATH", _write_signal_json(tmp_path, None))
    assert ss.regional_price_pressure() is None


# ─────────────────────────────────────────────────────────────────────────────
# scrape_bolivia_data — inflación interanual vía WP REST con fallback
# ─────────────────────────────────────────────────────────────────────────────
def test_scrape_inflation_prefers_wp_rest(monkeypatch):
    from business.management.commands.scrape_bolivia_data import Command
    from business.management.commands import ingest_ine_series
    ipc = {"period": "junio de 2026", "annual_pct": 9.23, "regional": {"Oruro": 3.86}}
    monkeypatch.setattr(ingest_ine_series.Command, "_fetch_ipc_wp",
                        lambda self, timeout: ipc)
    val, src, detail = Command()._scrape_inflation(timeout=1)
    assert val == 9.23
    assert src == "ine-wp-rest"
    assert detail is ipc


def test_scrape_inflation_falls_back_to_curated(monkeypatch):
    from business.management.commands.scrape_bolivia_data import Command
    from business.management.commands import ingest_ine_series

    def boom(self, timeout):
        raise RuntimeError("INE caído")

    monkeypatch.setattr(ingest_ine_series.Command, "_fetch_ipc_wp", boom)
    monkeypatch.setattr(Command, "_fetch", boom)
    val, src, detail = Command()._scrape_inflation(timeout=1)
    assert val is None and detail is None
    assert src == "fallback-curado"
