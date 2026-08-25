"""Regresiones que impiden volver a anclar Findempro en el peg de 2011.

Bolivia sostuvo Bs 6,96 por dólar desde 2011 hasta que dejó de sostenerlo. Todo
lo que se escribió durante esos años lo trató como constante: rangos de
validación, valores curados, divisores en fórmulas. Con el oficial en 11,50 esas
constantes dejaron de describir el mundo, y la única que fallaba ruidosamente era
ninguna — el sistema seguía andando y sembrando simulaciones con un dólar 65 %
por debajo del real.

Estas pruebas hacen ruido.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2]          # .../findempro
BUSINESS = APP / "business"

# Único uso permitido del peg histórico: la normalización de demanda de
# exportación en `product/data/product_real_data.py`, donde 6,96 es la LÍNEA BASE
# del régimen 2011-2025 contra la que se mide la sensibilidad, no el tipo de
# cambio vigente. Cambiar ese divisor altera la semántica del modelo y es una
# decisión del dueño de la simulación, no de esta capa.
# Cada excepción va con su razón. La lista está CONGELADA a propósito: existe
# para que ninguna nueva aparezca sin que alguien la discuta, no para tapar las
# que ya estaban. Cambiar la semántica de la simulación es del dueño del modelo.
PEG_ALLOWLIST = {
    "product/data/product_real_data.py":
        "6,96 es la línea base del régimen 2011-2025 en `export_demand`, contra "
        "la que se mide la sensibilidad al tipo de cambio. No es el tipo vigente; "
        "cambiar el divisor altera la semántica del modelo.",
    "product/data/areas_real_data.py":
        "`tipo_cambio_referencia` de un dataset de demostración del simulador.",
    "product/data/area_test_data.py":
        "idem: variante de prueba del dataset de demostración del simulador.",
    "business/data/bolivia_industries.py":
        "MARKET_CONTEXT: valor CURADO de respaldo, alcanzable sólo si KDP no "
        "responde, y se reporta siempre como `fallback-curado`.",
    "business/management/commands/scrape_bolivia_data.py":
        "CURATED: el mismo respaldo, en el comando que lo escribe.",
}

PEG_VALUES = {6.96, 6.86, 6.98}


def _py_files():
    for p in APP.rglob("*.py"):
        rel = p.relative_to(APP).as_posix()
        if "/tests/" in f"/{rel}" or rel.startswith("tests/"):
            continue
        if "/migrations/" in f"/{rel}" or "/.venv/" in f"/{rel}":
            continue
        yield p, rel


def test_el_peg_no_reaparece_como_numero_suelto():
    """6,96 sólo puede aparecer en prosa o en la allowlist justificada.

    Se buscan literales NUMÉRICOS con tokenize, no texto: un docstring que
    explique el peg no es el problema, un `= 6.96` sí lo es.
    """
    import io
    import tokenize

    ofensores = []
    for p, rel in _py_files():
        if rel in PEG_ALLOWLIST:
            continue
        src = p.read_text(encoding="utf-8", errors="replace")
        try:
            toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            continue
        for t in toks:
            if t.type != tokenize.NUMBER:
                continue
            try:
                val = float(t.string)
            except ValueError:
                continue
            if val in PEG_VALUES:
                ofensores.append(f"{rel}:{t.start[0]}: {t.line.strip()[:90]}")
    assert not ofensores, (
        "El peg de 2011 volvió al código como constante:\n  " + "\n  ".join(ofensores))


def test_no_hay_bandas_de_validacion_ancladas_al_peg():
    """Una banda 6,5–7,5 no puede observar 11,50; el filtro se vuelve el error."""
    sospechosas = []
    banda = re.compile(r"6[.,]\d.{0,20}<=?.{0,20}7[.,]\d|7[.,]\d.{0,20}>=?.{0,20}6[.,]\d")
    for p, rel in _py_files():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if banda.search(line) and not line.strip().startswith("#"):
                sospechosas.append(f"{rel}:{i}: {line.strip()[:90]}")
    assert not sospechosas, (
        "Hay rangos de validación anclados al régimen histórico:\n  "
        + "\n  ".join(sospechosas))


def test_la_banda_de_kdp_admite_el_regimen_actual():
    from business import kdp_source
    lo, hi = kdp_source.FX_BAND
    assert lo < 6.96 < hi, "la banda debe seguir admitiendo el histórico"
    assert lo < 11.50 < hi, "la banda debe admitir el oficial vigente"
    assert lo < 20.0 < hi, "la banda no debe presuponer el techo del régimen actual"


def test_kdp_source_no_convierte_null_en_cero():
    """Un 0 se lee como medición. Un dato ausente tiene que ausentarse."""
    src = (BUSINESS / "kdp_source.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        # or 0 / or 0.0 sobre un valor de KDP es la forma silenciosa de inventar
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for v in node.values:
                if isinstance(v, ast.Constant) and v.value in (0, 0.0):
                    pytest.fail("kdp_source usa `or 0`: un ausente se volvería medición")
    assert "float(payload[\"value\"])" in src or 'float(payload["value"])' in src


def test_el_curado_nunca_se_reporta_como_observado():
    """Si KDP no responde, la fuente registrada debe decir que es curada."""
    cmd = (BUSINESS / "management/commands/scrape_bolivia_data.py").read_text(encoding="utf-8")
    assert "fallback-curado" in cmd, "el marcador de curado desapareció"
    # y el camino KDP tiene que etiquetarse distinto
    assert "kdp_source" in cmd
    src = (BUSINESS / "kdp_source.py").read_text(encoding="utf-8")
    assert 'f"kdp:' in src, "la fuente KDP debe identificarse con prefijo kdp:"


def test_kdp_rechaza_provenance_no_observada_en_las_tres_anclas():
    """Las tres anclas macro tienen que validar provenance, no sólo una."""
    src = (BUSINESS / "kdp_source.py").read_text(encoding="utf-8")
    for fn in ("fetch_fx_oficial", "fetch_inflacion_anual", "fetch_paralelo"):
        i = src.index(f"def {fn}")
        j = src.find("\ndef ", i + 1)
        cuerpo = src[i:j if j > 0 else len(src)]
        assert "provenance" in cuerpo, f"{fn} no valida provenance"


def test_la_allowlist_del_peg_esta_justificada_y_acotada():
    """Ninguna excepción sin razón escrita, y ninguna que ya no exista."""
    assert len(PEG_ALLOWLIST) == 5, (
        "La allowlist del peg cambió de tamaño. Si sumaste una excepción, "
        "escribí por qué; si quitaste el ancla, quitá también la entrada.")
    for rel, razon in PEG_ALLOWLIST.items():
        assert (APP / rel).exists(), f"la allowlist apunta a un fichero que ya no existe: {rel}"
        assert len(razon) > 40, f"la excepción de {rel} no explica nada"
