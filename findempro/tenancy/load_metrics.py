"""Opt-in request metrics for the isolated DEV capacity harness."""

from __future__ import annotations

import time

from django.db import connection


class LoadMetricsMiddleware:
    """Expose per-request SQL counts/timing without a network metrics backend."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        connection.force_debug_cursor = True
        started = time.perf_counter()
        response = self.get_response(request)
        queries = list(connection.queries)
        db_ms = sum(float(item.get("time") or 0) for item in queries) * 1000
        response["X-Findempro-DB-Queries"] = str(len(queries))
        response["X-Findempro-DB-Latency-Ms"] = f"{db_ms:.3f}"
        response["X-Findempro-App-Latency-Ms"] = f"{(time.perf_counter() - started) * 1000:.3f}"
        return response
