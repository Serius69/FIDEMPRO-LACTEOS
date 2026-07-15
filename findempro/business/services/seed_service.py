"""
business/services/seed_service.py
=================================
Sembrado multi-industria para FindEMPro.

El motor de simulación (181 variables / 91 ecuaciones / 14 áreas) es genérico:
modela ingresos, costos, inventario y márgenes de *cualquier* PyME. Sólo era
"lácteo" en sus valores de ejemplo. Este servicio **reutiliza esa estructura
validada** y parametriza los valores económicos (precio, costo, demanda,
estacionalidad) por industria, a partir de datos reales del mercado boliviano
(ver ``business.data.bolivia_industries`` + ``bolivia_market_data.json``).

Flujo por negocio:
    Business (tipo N)
      └─ por cada Producto de la industria:
           Product  → Áreas + Variables + Ecuaciones + Cuestionario   (helpers validados)
           QuestionaryResult → Answers  (GENERADAS desde el baseline del producto)
      └─ ProbabilisticDensityFunction (Normal, media = demanda del producto ancla)

Idempotente: no duplica negocios del mismo tipo para el mismo usuario.
"""
from __future__ import annotations

import ast
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from django.contrib.auth.models import User
from django.db import transaction

from business.models import Business, CompanyProfile
from product.models import Product
from questionary.models import Questionary, Question, QuestionaryResult, Answer
from simulate.models import ProbabilisticDensityFunction

# Helpers de creación ya validados (los mismos que usa el onboarding lácteo).
from pages.views.business_creator import (
    create_and_save_areas,
    create_variables_and_equations,
    create_and_save_questionary,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Baseline de producto — el contrato de datos por producto de cada industria.
# Cada campo alimenta o bien la fila Product, o bien una respuesta del cuestionario
# (mapeada por las iniciales de variable que consume el motor).
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ProductBaseline:
    name: str
    unit: str                      # litros, kilogramos, unidades, servicios, ...
    price: float                   # PVP  — precio de venta (Bs)
    unit_cost: float               # CUIP — costo unitario del insumo/producción (Bs)
    daily_demand: float            # QPL/DH/DE base — demanda/venta diaria promedio
    daily_clients: int             # CPD  — clientes por día
    employees: int                 # NEPP — empleados
    monthly_salaries: float        # SE   — sueldos y salarios mensuales (Bs)
    daily_fixed_cost: float        # CFD  — costo fijo diario (Bs)
    transport_unit_cost: float     # CUTRANS — costo de transporte por unidad (Bs)
    marketing_monthly: float       # GMM  — gasto de marketing mensual (Bs)
    demand_cv: float = 0.12        # coef. de variación de la demanda histórica
    capacity_factor: float = 1.25  # capacidad vs demanda (CPROD/QMAX)
    inventory_days: float = 12.0   # días de inventario objetivo (CIP/CMIPF/SI)
    seasonal: bool = False         # ED — ¿hay estacionalidad?
    peak_months: List[int] = field(default_factory=list)   # meses pico [1..12]
    description: str = ""
    profit_margin: float = 20.0    # margen típico (%) para la fila Product

    def selling_price(self) -> float:
        return self.price


@dataclass
class IndustrySpec:
    business_type: int             # business.models.Business.BusinessType
    business_name: str
    location: str
    products: List[ProductBaseline]


# ─────────────────────────────────────────────────────────────────────────────
# Plantilla estructural de respuestas.
# Las preguntas "no económicas" (tiempos, distancias, % de proveedores, cadena de
# frío, etc.) comparten un default sensato entre industrias; se derivan una sola
# vez del set lácteo de referencia, uniendo answer_data_leche (keyed por texto de
# pregunta) con question_data (texto → iniciales). Se cachea a nivel de módulo.
# ─────────────────────────────────────────────────────────────────────────────
_STRUCTURAL_DEFAULTS: Optional[Dict[str, object]] = None

# Iniciales que SIEMPRE se recalculan desde el baseline del producto (no se toman
# del default lácteo).
_ECONOMIC_INITIALS = {
    "PVP", "PC", "CUIP", "DE", "QPL", "CPROD", "QMAX", "CPPL", "CIP", "CMIPF",
    "SI", "NEPP", "SE", "CFD", "CUTRANS", "GMM", "CPD", "CTL", "DH", "ED", "NMD",
}


def _load_structural_defaults() -> Dict[str, object]:
    """Construye {iniciales: valor_default} a partir del set lácteo de referencia."""
    global _STRUCTURAL_DEFAULTS
    if _STRUCTURAL_DEFAULTS is not None:
        return _STRUCTURAL_DEFAULTS

    from questionary.data.questionary_test_data import question_data
    from questionary.data.questionary_result_test_data import answer_data_leche

    q_by_text = {q["question"]: q.get("initials_variable") for q in question_data}
    defaults: Dict[str, object] = {}
    for item in answer_data_leche:
        initials = q_by_text.get(item.get("question"))
        if initials:
            defaults[initials] = item.get("answer")
    _STRUCTURAL_DEFAULTS = defaults
    return defaults


def _seasonality_multiplier(index: int, baseline: ProductBaseline,
                            business_type: Optional[int] = None) -> float:
    """
    Factor estacional por posición temporal (histórico diario, 30 días = 1 mes,
    empezando en enero → un ciclo anual completo cada 360 puntos).

    Con ``business_type`` usa el **perfil estacional REAL del sector** boliviano
    (``bolivia_sector_series``, media 1.0). Sin él, cae al comportamiento legacy
    (onda ±25 % sobre ``peak_months``).
    """
    month = (index // 30) % 12 + 1
    if business_type is not None:
        from business.data.bolivia_sector_series import monthly_factor
        return monthly_factor(business_type, month)
    if not baseline.seasonal or not baseline.peak_months:
        return 1.0
    return 1.25 if month in baseline.peak_months else 0.95


def generate_answers(baseline: ProductBaseline, n_history: int = 45,
                     rng=None, business_type: Optional[int] = None) -> Dict[str, object]:
    """
    Genera el dict {iniciales: respuesta} para un producto, combinando la
    plantilla estructural con los drivers económicos del baseline y una serie
    histórica de demanda realista (>= n_history puntos).

    ``business_type`` (opcional) activa el perfil estacional REAL del sector
    boliviano para la forma de la demanda histórica (ver ``_seasonality_multiplier``).
    """
    import random
    rng = rng or random.Random(hash(baseline.name) & 0xFFFFFFFF)

    defaults = dict(_load_structural_defaults())

    d = baseline.daily_demand
    cap = max(d * baseline.capacity_factor, d + 1)
    inv = max(d * baseline.inventory_days, 1)

    # Serie histórica de demanda: base * estacionalidad * ruido gaussiano.
    history: List[float] = []
    for i in range(n_history):
        season = _seasonality_multiplier(i, baseline, business_type)
        noise = rng.gauss(1.0, baseline.demand_cv)
        val = d * season * max(noise, 0.35)
        history.append(round(val, 1) if baseline.unit != "unidades" else int(max(val, 0)))

    econ: Dict[str, object] = {
        "PVP": round(baseline.price, 2),
        "PC": round(baseline.price * 1.02, 2),
        "CUIP": round(baseline.unit_cost, 2),
        "QPL": round(d, 1),
        "DE": round(d * 1.06, 1),
        "CPROD": round(cap, 1),
        "QMAX": round(cap, 1),
        "CPPL": round(cap * 0.5, 1),
        "CIP": round(inv, 1),
        "CMIPF": round(inv * 1.8, 1),
        "SI": round(d * 3, 1),
        "CTL": round(d * 1.02, 1),
        "NEPP": int(baseline.employees),
        "SE": round(baseline.monthly_salaries, 2),
        "CFD": round(baseline.daily_fixed_cost, 2),
        "CUTRANS": round(baseline.transport_unit_cost, 2),
        "GMM": round(baseline.marketing_monthly, 2),
        "CPD": int(baseline.daily_clients),
        "NMD": 30,
        "ED": "Sí" if baseline.seasonal else "No",
        "DH": history,
    }
    defaults.update(econ)
    return defaults


class IndustrySeeder:
    """Siembra un negocio completo (con datos) para un tipo de industria."""

    def __init__(self, user: User):
        self.user = user

    # ── API principal ────────────────────────────────────────────────────────
    @transaction.atomic
    def seed_business(self, spec: IndustrySpec, *, force: bool = False) -> Optional[Business]:
        existing = Business.objects.filter(
            fk_user=self.user, type=spec.business_type, is_active=True
        ).first()
        if existing and not force:
            logger.info("Business tipo %s ya existe (id=%s) — se omite", spec.business_type, existing.id)
            return existing

        if force:
            # `Business` tiene UNIQUE(name, fk_user) con collation NOCASE: para
            # recrear hay que liberar el nombre. Renombramos+desactivamos los
            # negocios previos con ese nombre (case-insensitive; el modelo title-casea
            # al guardar, así que un match exacto no basta), incluyendo restos de una
            # corrida parcial, sin borrado en cascada.
            for old in Business.objects.filter(fk_user=self.user, name__iexact=spec.business_name):
                old.name = f"{spec.business_name} (reemplazado #{old.id})"
                old.is_active = False
                old.save(update_fields=["name", "is_active"])

        business = Business.objects.create(
            name=spec.business_name,
            type=spec.business_type,
            location=spec.location,
            fk_user=self.user,
            is_active=True,
        )
        # Perfil de simulación con defaults por sector (ya existente en el modelo).
        CompanyProfile.get_or_create_for_business(business)

        anchor_demand = spec.products[0].daily_demand if spec.products else 1000
        self._create_pdf(business, anchor_demand)

        for baseline in spec.products:
            self._create_product_with_data(business, baseline)

        logger.info(
            "Sembrado negocio '%s' (tipo=%s) con %d productos",
            business.name, spec.business_type, len(spec.products),
        )
        return business

    # ── Internos ──────────────────────────────────────────────────────────────
    def _create_pdf(self, business: Business, mean: float) -> None:
        ProbabilisticDensityFunction.objects.get_or_create(
            distribution_type=1,  # Normal
            fk_business=business,
            defaults={
                "name": f"Distribución Normal — {business.name}",
                "mean_param": round(mean, 2),
                "std_dev_param": round(mean * 0.12, 2),
                "cumulative_distribution_function": 0.5,
                "is_active": True,
            },
        )

    def _create_product_with_data(self, business: Business, baseline: ProductBaseline) -> Product:
        product = Product.objects.create(
            name=baseline.name,
            description=baseline.description or f"{baseline.name} — producto del mercado boliviano.",
            type=1,
            is_active=True,
            fk_business=business,
        )
        # Estructura de simulación (reutiliza los helpers validados del onboarding).
        create_and_save_areas(product)
        create_variables_and_equations(product)
        create_and_save_questionary(product)

        # Respuestas generadas desde el baseline del producto.
        self._create_answers(product, baseline)
        return product

    def _create_answers(self, product: Product, baseline: ProductBaseline) -> None:
        # Estacionalidad REAL del sector + un año completo de histórico diario
        # (360 puntos) para que el perfil mensual boliviano sea observable.
        business_type = getattr(product.fk_business, "type", None)
        answers_by_initials = generate_answers(
            baseline, n_history=360, business_type=business_type)

        for questionary in Questionary.objects.filter(fk_product=product, is_active=True):
            qresult = QuestionaryResult.objects.create(
                fk_questionary=questionary, is_active=True
            )
            questions = Question.objects.filter(
                fk_questionary=questionary, is_active=True
            ).select_related("fk_variable")

            batch: List[Answer] = []
            for question in questions:
                initials = getattr(question.fk_variable, "initials", None)
                if initials is None or initials not in answers_by_initials:
                    continue
                value = answers_by_initials[initials]
                batch.append(Answer(
                    answer=str(value),
                    fk_question=question,
                    fk_questionary_result=qresult,
                    is_active=True,
                ))
            Answer.objects.bulk_create(batch)
