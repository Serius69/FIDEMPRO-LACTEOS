#!/usr/bin/env python3
"""Profile representative Findempro simulation sizes without external services."""
from __future__ import annotations

import argparse
import gc
import json
import os
import resource
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "findempro"
PROFILES = {"small": 25, "medium": 250, "heavy": 2_000}


def percentile(values, quantile):
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def stats(values):
    return {
        "mean": round(statistics.fmean(values), 4),
        "p50": round(percentile(values, 0.50), 4),
        "p95": round(percentile(values, 0.95), 4),
        "max": round(max(values), 4),
    }


def model_spec():
    from modeling.schema import empty_model_spec

    spec = empty_model_spec(name="Synthetic capacity model", sector="generic")
    spec["metadata"]["horizon"] = 12
    spec["variables"] = [
        {"id": "demand", "value": 100},
        {"id": "price", "value": 12},
        {"id": "unit_cost", "value": 7},
    ]
    spec["revenues"] = [{"id": "revenue", "expression": "demand * price"}]
    spec["costs"] = [{"id": "cost", "expression": "demand * unit_cost"}]
    return spec


def profile(name, iterations, repeats):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from modeling.engine import run_engine

    runtimes, cpu_times, peaks, query_counts = [], [], [], []
    spec = model_spec()
    tracemalloc.start()
    for index in range(repeats):
        gc.collect()
        tracemalloc.reset_peak()
        wall_started, cpu_started = time.perf_counter(), time.process_time()
        with CaptureQueriesContext(connection) as queries:
            run_engine(spec, "monte_carlo", iterations=iterations, seed=20260829 + index)
        cpu_times.append((time.process_time() - cpu_started) * 1_000)
        runtimes.append((time.perf_counter() - wall_started) * 1_000)
        peaks.append(tracemalloc.get_traced_memory()[1] / 1024 / 1024)
        query_counts.append(len(queries))
    tracemalloc.stop()
    runtime = stats(runtimes)
    return {
        "profile": name,
        "iterations": iterations,
        "repeats": repeats,
        "runtime_ms": runtime,
        "cpu_ms": stats(cpu_times),
        "python_allocation_peak_mb": stats(peaks),
        "process_max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 3),
        "queries": {"total": sum(query_counts), "per_simulation": stats(query_counts)},
        "simulations_per_minute_single_process": round(60_000 / runtime["mean"], 3),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "load" / "simulation-profile.json")
    args = parser.parse_args(argv)
    if args.repeats < 1:
        parser.error("--repeats must be >= 1")
    os.environ.setdefault("DJANGO_ENV", "testing")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "findempro.settings.testing")
    os.environ.setdefault("SECRET_KEY", "simulation-profiler-dev-only")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/findempro-simulation-profiler-mpl")
    sys.path.insert(0, str(BACKEND))
    import django

    django.setup()
    payload = {
        "schema_version": 1,
        "host": os.uname().nodename,
        "environment": "DEV",
        "data": "SYNTHETIC",
        "profiles": [profile(name, iterations, args.repeats) for name, iterations in PROFILES.items()],
        "limitations": [
            "Memory is Python allocation peak plus process max RSS; native allocator attribution is not isolated.",
            "This profiles the pure engine; queue and HTTP latency are measured by findempro_load_harness.py.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SIMULATION_PROFILE=PASS RESULT={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
