"""
gbm.py
======
Movimiento Browniano Geométrico (GBM) como **proceso de demanda con memoria
temporal** para el motor Monte Carlo.

Motivación
----------
El muestreo por defecto (``ScenarioGenerator`` / ``_sample_demand_grid``) genera
la demanda de cada período de forma **i.i.d.**: cada celda (período, escenario)
es un draw independiente de una distribución ajustada al NIVEL de demanda. Eso no
tiene deriva ni correlación temporal — la demanda del período *t+1* no "recuerda"
la del período *t*.

El GBM modela la demanda como un proceso log-normal con deriva y volatilidad
calibradas sobre los **log-retornos**::

    S_t = S_0 · exp( Σ_{k≤t} [ m + s·Z_k ] ),   Z_k ~ N(0, 1) i.i.d.

Propiedades frente al muestreo i.i.d.:
  · Trayectorias siempre positivas (exp de un normal).
  · Deriva `m` (tendencia de crecimiento/caída del negocio) y volatilidad `s`
    consistentes, calibradas con datos.
  · Memoria temporal: la trayectoria acumula shocks (``cumsum`` sobre el eje de
    períodos) en vez de resamplear el nivel cada período.

Portado del material de la maestría MAE-IA
(``dev/datasets/data_MAE_IA/Monte Carlo + GBM + derivados/`` — funciones
``calibrar_gbm`` y ``simular_gbm_paths``), preservando la **corrección de Itô**
en la deriva anualizada.

Diseño
------
Este módulo es **puro NumPy**: no importa Django ni otros módulos del proyecto, y
el backend de arrays (``numpy`` o ``cupy``) se **inyecta** como ``xp`` + ``rng``.
Así se testea en aislamiento y corre en GPU sin reescribirse.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

import numpy as np


# ── Calibración ──────────────────────────────────────────────────────────────

def calibrar_gbm(log_ret: Sequence[float], periodos_anio: int = 365) -> Dict[str, float]:
    """
    Estima los parámetros del GBM por máxima verosimilitud sobre log-retornos.

    Parámetros
    ----------
    log_ret : secuencia de log-retornos por período (diarios si el paso es 1 día).
    periodos_anio : períodos por año para anualizar (365 para un mercado 24/7).

    Retorna
    -------
    dict con:
      · ``media_d``  — media de log-retornos por período (deriva log por período).
      · ``sigma_d``  — desviación estándar de log-retornos por período (vol por período).
      · ``mu_a``     — deriva anualizada CON corrección de Itô: (media_d + ½σ_d²)·periodos.
      · ``sigma_a``  — volatilidad anualizada: σ_d·√periodos.
      · ``n``        — número de log-retornos usados.

    La corrección de Itô en ``mu_a`` refleja que E[S_T] = S_0·exp(mu_a·T) para el
    GBM; ``media_d`` (sin corrección) es la deriva del *logaritmo* por período, que
    es lo que se usa directamente al simular con paso de un período.
    """
    r = np.asarray(log_ret, dtype=float)
    r = r[np.isfinite(r)]
    n = int(r.size)
    if n < 2:
        # Sin datos suficientes: proceso sin deriva ni volatilidad (degenerado).
        return {"media_d": 0.0, "sigma_d": 0.0, "mu_a": 0.0, "sigma_a": 0.0, "n": n}

    media_d = float(r.mean())
    sigma_d = float(r.std(ddof=1))
    sigma_a = sigma_d * float(np.sqrt(periodos_anio))
    mu_a = (media_d + 0.5 * sigma_d ** 2) * periodos_anio
    return {
        "media_d": media_d,
        "sigma_d": sigma_d,
        "mu_a": mu_a,
        "sigma_a": sigma_a,
        "n": n,
    }


def calibrar_gbm_desde_niveles(
    niveles: Sequence[float],
    periodos_anio: int = 365,
) -> Dict[str, float]:
    """
    Calibra el GBM a partir de una serie de **niveles** (p. ej. demanda histórica).

    Calcula los log-retornos ``log(S_t / S_{t-1})`` sobre los niveles positivos y
    delega en :func:`calibrar_gbm`. Añade ``s0`` = último nivel observado.
    """
    s = np.asarray(niveles, dtype=float)
    s = s[np.isfinite(s) & (s > 0)]
    if s.size < 2:
        return {"media_d": 0.0, "sigma_d": 0.0, "mu_a": 0.0, "sigma_a": 0.0,
                "n": int(s.size), "s0": float(s[-1]) if s.size else 0.0}
    log_ret = np.log(s[1:] / s[:-1])
    params = calibrar_gbm(log_ret, periodos_anio=periodos_anio)
    params["s0"] = float(s[-1])
    return params


def params_gbm_desde_momentos(mean: float, std: float) -> Dict[str, float]:
    """
    Deriva parámetros GBM por período cuando solo se conocen la media y la
    desviación estándar del **nivel** (no la serie histórica).

    Usa la relación log-normal: si el nivel tiene coeficiente de variación
    ``CV = σ/μ``, entonces la volatilidad log por período es
    ``s = √(ln(1 + CV²))``. Sin información de tendencia, la deriva log ``m`` se
    toma **0** (proceso sin tendencia); si hay historia, preferir
    :func:`calibrar_gbm_desde_niveles`.

    Retorna dict con ``media_d`` (=0), ``sigma_d`` (=s) y ``s0`` (=mean).
    """
    mu = float(mean)
    sigma = max(float(std), 0.0)
    s0 = mu if mu > 0 else max(abs(mu), 1e-6)
    cv2 = (sigma / s0) ** 2 if s0 > 0 else 0.0
    sigma_d = float(np.sqrt(np.log1p(cv2)))
    return {"media_d": 0.0, "sigma_d": sigma_d, "s0": s0}


# ── Simulación ───────────────────────────────────────────────────────────────

def simular_gbm_grid(
    s0: float,
    media_d: float,
    sigma_d: float,
    T: int,
    N: int,
    xp: Any = np,
    rng: Optional[Any] = None,
) -> Any:
    """
    Simula una grilla (T, N) de **trayectorias** GBM (una por escenario/columna).

    A diferencia del muestreo i.i.d., la demanda del período *t* acumula los
    shocks de los períodos previos (``cumsum`` sobre el eje de períodos)::

        log_incr[t, n] = media_d + sigma_d · Z[t, n]
        log_path[t, n] = Σ_{k=0}^{t} log_incr[k, n]
        S[t, n]        = s0 · exp( log_path[t, n] )

    El período con índice 0-based ``t`` corresponde a ``t+1`` pasos desde el
    origen; su marginal es log-normal con log ~ N(media_d·(t+1), σ_d²·(t+1)),
    consistente con :func:`gbm_marginal`.

    Parámetros
    ----------
    s0       : nivel inicial (> 0) del que parten las trayectorias.
    media_d  : deriva log por período (media de log-retornos).
    sigma_d  : volatilidad log por período (σ de log-retornos).
    T, N     : número de períodos (filas) y escenarios (columnas).
    xp       : módulo de arrays (``numpy`` o ``cupy``).
    rng      : generador del backend (``xp.random.default_rng(seed)``); si es
               None, se crea uno sin semilla sobre ``xp``.

    Retorna
    -------
    array (T, N) del backend ``xp`` con la demanda simulada (no-negativa).
    """
    if rng is None:
        rng = xp.random.default_rng()
    shape = (int(T), int(N))
    s0_pos = max(float(s0), 1e-6)

    z = rng.standard_normal(size=shape)
    log_incr = float(media_d) + max(float(sigma_d), 0.0) * z
    log_path = xp.cumsum(log_incr, axis=0)     # acumula sobre el eje de períodos
    paths = s0_pos * xp.exp(log_path)
    return xp.maximum(paths, 0.0)


def gbm_marginal(
    s0: float,
    media_d: float,
    sigma_d: float,
    period_idx: int,
    n: int,
    xp: Any = np,
    rng: Optional[Any] = None,
) -> Any:
    """
    Muestrea la distribución **marginal** del GBM en un único período.

    Equivale a la columna ``period_idx`` de :func:`simular_gbm_grid` pero sin
    generar la trayectoria completa: el log del nivel en el período (0-based)
    ``period_idx`` es N(media_d·pasos, σ_d²·pasos) con ``pasos = period_idx + 1``.
    Útil para ``ScenarioGenerator.generate_for_period`` (un solo período).
    """
    if rng is None:
        rng = xp.random.default_rng()
    pasos = int(period_idx) + 1
    s0_pos = max(float(s0), 1e-6)
    z = rng.standard_normal(size=int(n))
    log_val = float(media_d) * pasos + max(float(sigma_d), 0.0) * float(np.sqrt(pasos)) * z
    return xp.maximum(s0_pos * xp.exp(log_val), 0.0)
