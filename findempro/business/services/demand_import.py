"""
Importación de series de demanda REALES para productos existentes.
================================================================

Este servicio carga series históricas de demanda reales (CSV/Excel) y las
persiste en el **mismo lugar que consume el motor de simulación**: la respuesta
(``Answer``) del cuestionario a la pregunta de demanda histórica
(``initials='DH'``), bajo cada ``QuestionaryResult`` activo del producto.

Contexto — cómo lee la demanda el motor (``simulate/views/simulate_init_view.py``
``_extract_demand_data``):

* Recorre ``questionary_result.fk_question_result_answer.all()`` (¡sin filtrar
  ``is_active``!) y toma la **primera** respuesta parseable cuya pregunta sea
  exactamente ``DEMAND_QUESTION_TEXT``.
* ``_parse_demand_string`` acepta un array JSON (si empieza con ``[``) o una
  lista separada por comas/espacios.

Como el reader NO filtra por ``is_active`` y toma la primera coincidencia, para
"reemplazar" la serie sintética previa hay que **borrarla** (no basta con
desactivarla): si no, la sintética —con pk menor— seguiría ganando. Por eso el
modo ``replace`` elimina las respuestas ``DH`` previas antes de insertar la real.

El servicio no crea productos ni cuestionarios: importa series a productos que ya
tienen su estructura (creada por onboarding o ``seed_bolivia``).
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from django.db import transaction

from questionary.models import Answer, Question, Questionary, QuestionaryResult

logger = logging.getLogger(__name__)

# Pregunta canónica que lee el motor de simulación (debe coincidir literalmente).
DEMAND_QUESTION_TEXT = (
    'Ingrese los datos históricos de la demanda de su empresa (mínimo 30 datos).'
)
DEMAND_INITIALS = 'DH'

# Umbrales de calibración (alineados con el motor):
#   < 2  → GBM no calibra (gbm.py)
#   < 10 → el ajuste de distribución aborta (monte_carlo.py / simulate/models.py)
#   < 30 → mínimo recomendado por el cuestionario
MIN_POINTS_HARD = 2
MIN_POINTS_FIT = 10
MIN_POINTS_RECOMMENDED = 30


# ─────────────────────────────────────────────────────────────────────────────
# Resultados
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SeriesResult:
    """Resultado de importar la serie de un producto."""
    product: str
    status: str                       # 'imported' | 'skipped' | 'error'
    n_raw: int = 0                    # puntos leídos del archivo
    n_clean: int = 0                 # puntos válidos tras limpieza
    n_dropped: int = 0               # puntos descartados (NaN/inf/negativos)
    n_previous_deleted: int = 0      # respuestas DH previas eliminadas
    results_updated: int = 0         # QuestionaryResult afectados
    business: str = ''
    appended: bool = False
    message: str = ''
    warnings: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Limpieza (refleja _validate_and_clean_demand_data del motor)
# ─────────────────────────────────────────────────────────────────────────────
def clean_series(values) -> Tuple[List[float], int]:
    """
    Convierte a float y descarta NaN/inf/negativos, igual que el motor.
    Devuelve (serie_limpia, n_descartados).
    """
    clean: List[float] = []
    dropped = 0
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            dropped += 1
            continue
        if math.isnan(f) or math.isinf(f) or f < 0:
            dropped += 1
            continue
        clean.append(f)
    return clean, dropped


def sample_warnings(n: int) -> List[str]:
    """Advertencias de tamaño de muestra según los umbrales del motor."""
    warns: List[str] = []
    if n < MIN_POINTS_FIT:
        warns.append(
            f"solo {n} puntos válidos: por debajo de {MIN_POINTS_FIT}, el ajuste "
            f"de distribución puede abortar")
    elif n < MIN_POINTS_RECOMMENDED:
        warns.append(
            f"{n} puntos válidos: por debajo de los {MIN_POINTS_RECOMMENDED} "
            f"recomendados para el cuestionario")
    return warns


# ─────────────────────────────────────────────────────────────────────────────
# Resolución de producto
# ─────────────────────────────────────────────────────────────────────────────
def resolve_product(name: str, *, user=None, business: Optional[str] = None):
    """
    Resuelve un ``Product`` activo por nombre (case-insensitive), opcionalmente
    acotado por usuario (``fk_business__fk_user``) y/o nombre de negocio.

    Lanza ``LookupError`` si no hay coincidencia o si es ambigua.
    """
    from product.models import Product

    qs = Product.objects.filter(name__iexact=name.strip(), is_active=True)
    if user is not None:
        qs = qs.filter(fk_business__fk_user=user)
    if business:
        qs = qs.filter(fk_business__name__iexact=business.strip())

    matches = list(qs.select_related('fk_business'))
    if not matches:
        raise LookupError(
            f"no existe un producto activo llamado '{name}'"
            + (f" para el negocio '{business}'" if business else '')
            + (" (¿ya lo creaste con onboarding o seed_bolivia?)"))
    if len(matches) > 1:
        negocios = ', '.join(sorted({m.fk_business.name for m in matches}))
        raise LookupError(
            f"'{name}' es ambiguo: coincide con {len(matches)} productos "
            f"(negocios: {negocios}). Acota con --business o --user.")
    return matches[0]


# ─────────────────────────────────────────────────────────────────────────────
# Escritura de la serie en el cuestionario
# ─────────────────────────────────────────────────────────────────────────────
def _demand_question(questionary: Questionary) -> Optional[Question]:
    """
    Localiza la pregunta de demanda histórica en un cuestionario: primero por
    ``fk_variable.initials == 'DH'`` (canónico), con respaldo por texto exacto.
    """
    q = (Question.objects
         .filter(fk_questionary=questionary, is_active=True,
                 fk_variable__initials=DEMAND_INITIALS)
         .first())
    if q is None:
        q = (Question.objects
             .filter(fk_questionary=questionary, is_active=True,
                     question=DEMAND_QUESTION_TEXT)
             .first())
    return q


def _parse_existing(answer_text: str) -> List[float]:
    """Parsea una serie previa (JSON o separada por comas/espacios)."""
    if not answer_text:
        return []
    s = answer_text.strip()
    try:
        if s.startswith('['):
            return [float(x) for x in json.loads(s)]
        s = s.replace('[', '').replace(']', '')
        sep = ',' if ',' in s else None
        parts = s.split(sep) if sep else s.split()
        return [float(x) for x in parts if str(x).strip()]
    except (ValueError, TypeError, json.JSONDecodeError):
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Carga y agrupación del archivo (CSV / Excel)
# ─────────────────────────────────────────────────────────────────────────────
def load_dataframe(path: str, *, sep: str = ',', decimal: str = '.',
                   sheet=0):
    """
    Carga un CSV o Excel a un DataFrame. El formato se infiere por extensión
    (``.xlsx``/``.xls`` → Excel; el resto → CSV).
    """
    import pandas as pd

    lower = str(path).lower()
    if lower.endswith(('.xlsx', '.xls')):
        return pd.read_excel(path, sheet_name=sheet, decimal=decimal)
    return pd.read_csv(path, sep=sep, decimal=decimal)


def group_series(df, *, product_col: str = 'product', demand_col: str = 'demand',
                 date_col: Optional[str] = 'date',
                 business_col: Optional[str] = 'business',
                 single_product: Optional[str] = None,
                 ) -> Dict[Tuple[str, Optional[str]], List]:
    """
    Agrupa el DataFrame en ``{(producto, negocio|None): [valores ordenados]}``.

    * Si ``single_product`` se indica, toda la columna de demanda se asigna a ese
      producto (archivos de una sola serie, sin columna de producto).
    * Si existe columna de fecha, cada serie se ordena por fecha antes de extraer
      los valores.
    * ``business_col`` (si existe) permite desambiguar productos homónimos.
    """
    if demand_col not in df.columns:
        raise KeyError(
            f"la columna de demanda '{demand_col}' no está en el archivo "
            f"(columnas: {list(df.columns)})")

    has_date = bool(date_col) and date_col in df.columns
    has_business = bool(business_col) and business_col in df.columns

    if single_product:
        work = df.copy()
        if has_date:
            work = work.sort_values(date_col, kind='stable')
        return {(single_product, None): work[demand_col].tolist()}

    if product_col not in df.columns:
        raise KeyError(
            f"falta la columna de producto '{product_col}' (columnas: "
            f"{list(df.columns)}). Usá --product para archivos de una sola serie.")

    grouped: Dict[Tuple[str, Optional[str]], List] = {}
    key_cols = [product_col] + ([business_col] if has_business else [])
    for key, sub in df.groupby(key_cols, dropna=False, sort=False):
        if has_business:
            prod_name, biz_name = key if isinstance(key, tuple) else (key, None)
        else:
            prod_name = key[0] if isinstance(key, tuple) else key
            biz_name = None
        if has_date:
            sub = sub.sort_values(date_col, kind='stable')
        prod_name = str(prod_name).strip()
        biz_name = str(biz_name).strip() if biz_name is not None else None
        grouped[(prod_name, biz_name)] = sub[demand_col].tolist()
    return grouped


@transaction.atomic
def write_series(product, series: List[float], *, replace: bool = True,
                 dry_run: bool = False) -> SeriesResult:
    """
    Escribe ``series`` como la demanda histórica del producto, en todos los
    ``QuestionaryResult`` activos de su cuestionario de demanda.

    * ``replace=True``: elimina las respuestas DH previas e inserta la real.
    * ``replace=False`` (append): antepone la serie previa a la importada.
    """
    result = SeriesResult(
        product=product.name,
        business=getattr(product.fk_business, 'name', ''),
        status='imported',
        n_clean=len(series),
        appended=not replace,
    )

    # Cuestionario que contenga la pregunta de demanda.
    questionary = None
    dh_question = None
    for cand in Questionary.objects.filter(fk_product=product, is_active=True):
        q = _demand_question(cand)
        if q is not None:
            questionary, dh_question = cand, q
            break
    if dh_question is None:
        result.status = 'error'
        result.message = (
            "el producto no tiene una pregunta de demanda histórica ('DH') en "
            "ningún cuestionario activo")
        return result

    # Asegurar al menos un QuestionaryResult activo.
    qresults = list(QuestionaryResult.objects.filter(
        fk_questionary=questionary, is_active=True))
    if not qresults and not dry_run:
        qresults = [QuestionaryResult.objects.create(
            fk_questionary=questionary, is_active=True)]
    elif not qresults:
        # dry-run sin resultados: se crearía uno.
        result.results_updated = 1
        return result

    for qresult in qresults:
        prior = list(Answer.objects.filter(
            fk_questionary_result=qresult, fk_question=dh_question))

        final_series = series
        if not replace and prior:
            existing = _parse_existing(prior[0].answer)
            final_series = existing + series

        result.n_previous_deleted += len(prior)
        if dry_run:
            result.results_updated += 1
            continue

        if prior:
            Answer.objects.filter(
                fk_questionary_result=qresult, fk_question=dh_question).delete()
        Answer.objects.create(
            answer=json.dumps([round(float(x), 4) for x in final_series]),
            fk_question=dh_question,
            fk_questionary_result=qresult,
            is_active=True,
        )
        result.results_updated += 1

    result.n_clean = len(series)
    return result
