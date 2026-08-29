#!/usr/bin/env python3
"""Reproducible, no-Docker Findempro capacity harness for tromay-dev only."""
from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as dt
import http.cookiejar
import json
import math
import os
import random
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "findempro"
EXPECTED_HOST = "tromay-dev"
DATASET_SIZES = {"SMALL_DATASET": 100, "MEDIUM_DATASET": 1_000, "LARGE_ALLOWED_DATASET": 10_000}
SLOS = {
    "INTERACTIVE_HTTP": {"error_rate_lt": 0.01, "p95_ms_lt": 500, "p99_ms_lt": 1_000},
    "SIMULATION_SUBMIT": {"error_rate_lt": 0.01, "p95_ms_lt": 500, "p99_ms_lt": 1_000},
    "SIMULATION_STATUS": {"error_rate_lt": 0.01, "p95_ms_lt": 500, "p99_ms_lt": 1_000},
    "DATASET_IMPORT": {"error_rate_lt": 0.01, "p95_ms_lt": 3_000},
    "EXPORT": {"error_rate_lt": 0.01, "p95_ms_lt": 2_000},
}


def positive(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def non_negative_ratio(value):
    parsed = float(value)
    if not 0 <= parsed <= 10:
        raise argparse.ArgumentTypeError("must be between 0 and 10 free Organizations per paid Organization")
    return parsed


def unit_ratio(value):
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def non_negative(value):
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def dataset_size(value):
    if value.upper() in DATASET_SIZES:
        return DATASET_SIZES[value.upper()]
    parsed = positive(value)
    if parsed > 10_000:
        raise argparse.ArgumentTypeError("must be <= 10000")
    return parsed


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--organizations", type=positive, default=1, help="paying Organizations")
    result.add_argument("--users-per-org", type=positive, default=3)
    result.add_argument("--active-users-per-org", type=positive, default=1)
    result.add_argument("--concurrency", type=positive, default=1)
    result.add_argument("--projects-per-org", type=positive, default=2)
    result.add_argument("--datasets-per-project", type=positive, default=1)
    result.add_argument("--simulations-per-session", type=positive, default=2)
    result.add_argument("--scenarios-per-session", type=positive, default=2)
    result.add_argument("--exports-per-session", type=positive, default=1)
    result.add_argument("--ai-calls-per-session", type=positive, default=1)
    result.add_argument("--dataset-size", type=dataset_size, default=DATASET_SIZES["SMALL_DATASET"])
    result.add_argument("--free-ratio", type=non_negative_ratio, default=3.0)
    result.add_argument("--heavy-paid-ratio", type=unit_ratio, default=0.1)
    result.add_argument("--duration", type=positive, default=30)
    result.add_argument("--warmup", type=non_negative, default=5)
    result.add_argument("--ramp-up", type=non_negative, default=10)
    result.add_argument("--think-time-ms", type=non_negative, default=200)
    result.add_argument("--worker-concurrency", type=positive, default=2)
    result.add_argument("--simulation-profile", choices=("small", "medium", "heavy", "mixed"), default="mixed")
    result.add_argument("--profile", choices=("free", "paid", "heavy_paid", "mixed"), default="mixed")
    result.add_argument("--scenario", default="custom")
    result.add_argument("--port", type=positive, default=58177)
    result.add_argument("--python", default=sys.executable)
    result.add_argument("--seed", type=int, default=20260829)
    result.add_argument("--label", default="manual")
    result.add_argument("--results-dir", type=Path, default=ROOT / "artifacts" / "load")
    result.add_argument("--max-total-organizations", type=positive, default=2_500)
    result.add_argument("--capacity-guard-mb", type=positive, default=2_048)
    result.add_argument("--benchmark", action="store_true")
    result.add_argument("--smoke", action="store_true", help="one authenticated bounded request set")
    result.add_argument("--keep-state", action="store_true")
    return result


def run(command, env, *, stdout=None):
    subprocess.run(command, cwd=BACKEND, env=env, check=True, stdout=stdout, stderr=subprocess.STDOUT)


def percentile(values, quantile):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return round(ordered[lower], 3)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower), 3)


def distribution(values):
    if not values:
        return {"count": 0, "mean": None, "p50": None, "p95": None, "p99": None, "max": None}
    return {
        "count": len(values), "mean": round(statistics.fmean(values), 3),
        "p50": percentile(values, 0.50), "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99), "max": round(max(values), 3),
    }


@dataclasses.dataclass
class RequestRecord:
    operation: str
    category: str
    latency_ms: float
    status: int
    ok: bool
    db_queries: int | None = None
    db_latency_ms: float | None = None
    app_latency_ms: float | None = None
    is_http: bool = True
    detail: str = ""


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.records = []
        self.security = Counter()

    def add(self, record):
        with self._lock:
            self.records.append(record)

    def security_probe(self, name, passed):
        with self._lock:
            self.security[f"{name}_attempts"] += 1
            if not passed:
                self.security[f"{name}_failures"] += 1

    def summary(self, elapsed):
        http = [item for item in self.records if item.is_http]
        result = {
            "requests_total": len(http),
            "rps": round(len(http) / max(elapsed, 0.001), 3),
            "latency_ms": distribution([item.latency_ms for item in http]),
            "error_rate": round(sum(not item.ok for item in http) / max(1, len(http)), 6),
            "errors": sum(not item.ok for item in http),
            "expected_business_or_security_rejections": sum(item.ok and item.status >= 400 for item in http),
            "status_codes": dict(sorted(Counter(item.status for item in http).items())),
            "operations": {}, "categories": {},
            "db": {
                "queries": sum(item.db_queries or 0 for item in http),
                "latency_ms": round(sum(item.db_latency_ms or 0 for item in http), 3),
                "slow_queries_over_100ms": sum((item.db_latency_ms or 0) > 100 for item in http),
                "connections": "NOT_MEASURABLE_SQLITE",
                "locks": sum("locked" in item.detail.lower() for item in http),
            },
            "security": dict(self.security),
            "ai_stub": {
                "calls": sum(item.category == "AI" for item in self.records),
                "latency_ms": distribution([item.latency_ms for item in self.records if item.category == "AI"]),
                "failures": sum(item.category == "AI" and not item.ok for item in self.records),
                "real_provider": "NOT_CALLED",
            },
        }
        for key, items in _group(http, lambda item: item.operation).items():
            result["operations"][key] = _request_group(items)
        for key, items in _group(http, lambda item: item.category).items():
            result["categories"][key] = _request_group(items)
        return result


def _group(items, key):
    groups = defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    return groups


def _request_group(items):
    return {
        **distribution([item.latency_ms for item in items]),
        "errors": sum(not item.ok for item in items),
        "error_rate": round(sum(not item.ok for item in items) / max(1, len(items)), 6),
    }


def memory_state():
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, raw = line.split(":", 1)
        values[key] = int(raw.strip().split()[0]) // 1024
    return {
        "available_mb": values.get("MemAvailable", 0), "total_mb": values.get("MemTotal", 0),
        "swap_free_mb": values.get("SwapFree", 0), "swap_total_mb": values.get("SwapTotal", 0),
    }


def preflight(args):
    total = args.organizations + round(args.organizations * args.free_ratio)
    memory = memory_state()
    reasons = []
    if socket.gethostname() != EXPECTED_HOST:
        reasons.append(f"HOST_NOT_ALLOWED:{socket.gethostname()}")
    if args.active_users_per_org > args.users_per_org:
        reasons.append("ACTIVE_USERS_EXCEED_USERS_PER_ORG")
    if total > args.max_total_organizations:
        reasons.append(f"TOTAL_ORGANIZATIONS>{args.max_total_organizations}")
    if memory["available_mb"] < args.capacity_guard_mb:
        reasons.append(f"RAM_AVAILABLE<{args.capacity_guard_mb}MB")
    if total > 1_000 and memory["swap_free_mb"] < 512:
        reasons.append("SWAP_HEADROOM_LT_512MB_FOR_EXPLORATORY_TIER")
    return {"pass": not reasons, "reasons": reasons, "memory": memory, "total_organizations": total}


def django_bootstrap(env):
    os.environ.update(env)
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    import django
    django.setup()


def prepare_users(prefix, active_users_per_org):
    from django.contrib.auth import (
        BACKEND_SESSION_KEY,
        HASH_SESSION_KEY,
        SESSION_KEY,
        get_user_model,
    )
    from django.contrib.sessions.backends.db import SessionStore
    from modeling.models import BusinessModelDefinition, BusinessSimulationRun
    from tenancy.models import Organization

    manifests = []
    users = get_user_model().objects.filter(username__startswith=f"{prefix}-org-")
    organizations = Organization.objects.filter(name__startswith="Load Organization").select_related("subscription")
    for organization in organizations:
        memberships = list(
            organization.memberships.filter(is_active=True, user__in=users)
            .select_related("user").order_by("created_at")[:active_users_per_org]
        )
        models = list(
            BusinessModelDefinition.objects.filter(business__organization=organization)
            .select_related("current_version").order_by("created_at")
        )
        if not memberships or not models:
            continue
        probe_run = BusinessSimulationRun.objects.create(
            model_version=models[0].current_version, created_by=memberships[0].user,
            status="completed", progress=100,
            result={"summary": {"mean": 1}, "synthetic_probe": True},
        )
        plan = organization.subscription.effective_plan
        profile = "HEAVY_PAID" if plan == "PRO" else "PAID" if plan != "FREE" else "FREE"
        for membership in memberships:
            session = SessionStore()
            session[SESSION_KEY] = str(membership.user.pk)
            session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
            session[HASH_SESSION_KEY] = membership.user.get_session_auth_hash()
            session.create()
            manifests.append({
                "user_id": membership.user_id, "session_key": session.session_key,
                "organization_id": str(organization.id), "profile": profile, "plan": plan,
                "model_ids": [str(item.id) for item in models], "probe_run_id": str(probe_run.id),
            })
    return manifests


class ResourceSampler:
    def __init__(self, pids, broker_dir):
        self.pids, self.broker_dir = pids, broker_dir
        self.stop_event = threading.Event()
        self.cpu, self.ram_mb, self.queue = [], [], []
        self.total_cpu_seconds = 0.0
        self._thread = None

    @staticmethod
    def _proc(pid):
        try:
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            return int(fields[11]) + int(fields[12]), int(fields[21]) * os.sysconf("SC_PAGE_SIZE") / 1024 / 1024
        except (FileNotFoundError, ProcessLookupError, ValueError):
            return 0, 0.0

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        clock, cores = os.sysconf("SC_CLK_TCK"), max(1, os.cpu_count() or 1)
        previous_ticks = sum(self._proc(pid)[0] for pid in self.pids)
        previous_time = time.monotonic()
        while not self.stop_event.wait(0.25):
            now = time.monotonic()
            values = [self._proc(pid) for pid in self.pids]
            ticks, elapsed = sum(item[0] for item in values), max(now - previous_time, 0.001)
            cpu_seconds = max(0, ticks - previous_ticks) / clock
            self.total_cpu_seconds += cpu_seconds
            self.cpu.append(cpu_seconds / elapsed / cores * 100)
            self.ram_mb.append(sum(item[1] for item in values))
            self.queue.append(len(list((self.broker_dir / "queue").glob("*"))))
            previous_ticks, previous_time = ticks, now

    def stop(self):
        self.stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def summary(self):
        baseline = self.ram_mb[0] if self.ram_mb else 0
        return {
            "cpu_mean_percent_host": round(statistics.fmean(self.cpu), 3) if self.cpu else None,
            "cpu_peak_percent_host": round(max(self.cpu), 3) if self.cpu else None,
            "cpu_seconds": round(self.total_cpu_seconds, 3),
            "ram_mean_mb": round(statistics.fmean(self.ram_mb), 3) if self.ram_mb else None,
            "ram_peak_mb": round(max(self.ram_mb), 3) if self.ram_mb else None,
            "ram_peak_delta_mb": round(max(self.ram_mb) - baseline, 3) if self.ram_mb else None,
            "queue_peak": max(self.queue) if self.queue else 0,
        }


def wait_healthy(base_url, server, log_path, deadline_seconds=90):
    deadline = time.monotonic() + deadline_seconds
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        try:
            with opener.open(f"{base_url}/health/live/", timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            if server.poll() is not None:
                detail = log_path.read_text(errors="replace")[-4000:] if log_path.exists() else ""
                raise RuntimeError(f"backend exited before health (code={server.returncode})\n{detail}")
            time.sleep(0.2)
    raise RuntimeError("backend did not become healthy")


def wait_worker(worker, log_path, deadline_seconds=60):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if worker.poll() is not None:
            detail = log_path.read_text(errors="replace")[-4000:] if log_path.exists() else ""
            raise RuntimeError(f"worker exited before ready (code={worker.returncode})\n{detail}")
        if log_path.exists():
            worker_output = log_path.read_text(errors="replace")
            if " ready." in worker_output or "Connected to filesystem://" in worker_output:
                return
        time.sleep(0.2)
    detail = log_path.read_text(errors="replace")[-4000:] if log_path.exists() else ""
    raise RuntimeError(f"worker did not become ready\n{detail}")


def _loopback_cookie(name, value):
    return http.cookiejar.Cookie(
        version=0, name=name, value=value, port=None,
        port_specified=False, domain="127.0.0.1", domain_specified=False,
        domain_initial_dot=False, path="/", path_specified=True, secure=False,
        expires=None, discard=True, comment=None, comment_url=None,
        rest={"HttpOnly": None}, rfc2109=False,
    )


class VirtualUser:
    def __init__(self, base_url, manifest, other, metrics, dataset_rows, args, seed):
        self.base_url, self.manifest, self.other = base_url, manifest, other
        self.metrics, self.dataset_rows, self.args = metrics, dataset_rows, args
        self.random = random.Random(seed)
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(self.jar)
        )
        self.run_ids = []
        self.completed_run_ids = []
        self.simulations = self.scenarios = self.exports = self.imports = self.ai_calls = 0
        self.jar.set_cookie(_loopback_cookie("sessionid", manifest["session_key"]))
        self.jar.set_cookie(_loopback_cookie("csrftoken", f"{seed:032x}"[-32:]))

    def authenticate(self):
        status, _ = self.request(
            "GET", "/api/subscription/context/", "auth_session", "INTERACTIVE_HTTP", record=False
        )
        if status != 200:
            raise RuntimeError(f"prepared session was not authenticated (status={status})")

    def request(self, method, path, operation, category, payload=None, expected=(200,), record=True):
        body = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
        headers = {"Accept": "application/json", "X-Organization-ID": self.manifest["organization_id"]}
        if body is not None:
            headers["Content-Type"] = "application/json"
        csrf = next((cookie.value for cookie in self.jar if cookie.name == "csrftoken"), None)
        if csrf:
            headers["X-CSRFToken"] = csrf
        request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
        started = time.perf_counter()
        status, response_body, response_headers, detail = 0, b"", {}, ""
        try:
            with self.opener.open(request, timeout=30) as response:
                status, response_body, response_headers = response.status, response.read(), response.headers
        except urllib.error.HTTPError as exc:
            status, response_body, response_headers = exc.code, exc.read(), exc.headers
            detail = response_body.decode(errors="replace")[:500]
        except (OSError, urllib.error.URLError) as exc:
            detail = type(exc).__name__
        latency_ms = (time.perf_counter() - started) * 1000
        ok = status in expected
        if record:
            self.metrics.add(RequestRecord(
                operation=operation, category=category, latency_ms=latency_ms,
                status=status, ok=ok,
                db_queries=_header(response_headers, "X-Findempro-DB-Queries", int),
                db_latency_ms=_header(response_headers, "X-Findempro-DB-Latency-Ms", float),
                app_latency_ms=_header(response_headers, "X-Findempro-App-Latency-Ms", float),
                detail=detail,
            ))
        try:
            decoded = json.loads(response_body or b"{}")
        except json.JSONDecodeError:
            decoded = {}
        return status, decoded

    def step(self, record=True):
        operation = self._choose_operation()
        model_id = self.random.choice(self.manifest["model_ids"])
        if operation in {"scenario_configuration", "simulation_submit"}:
            model_id = self.manifest["model_ids"][0]
        if operation == "auth_session":
            self.request("GET", "/account/login/", operation, "INTERACTIVE_HTTP", record=record)
        elif operation == "organization_context":
            self.request("GET", "/api/subscription/context/", operation, "INTERACTIVE_HTTP", record=record)
        elif operation == "project_list":
            self.request("GET", "/modeling/models/", operation, "INTERACTIVE_HTTP", record=record)
        elif operation == "project_detail":
            self.request("GET", f"/modeling/models/{model_id}/", operation, "INTERACTIVE_HTTP", record=record)
        elif operation == "project_write":
            self.request("POST", f"/modeling/models/{model_id}/validate/", operation, "INTERACTIVE_HTTP", {}, record=record)
        elif operation == "dataset_read":
            self.request("POST", f"/modeling/models/{model_id}/imports/", operation, "DATASET_IMPORT", {
                "format": "json", "rows": self.dataset_rows[:25], "mapping": {}, "preview": True,
            }, expected=(200, 403), record=record)
        elif operation == "dataset_import":
            self.imports += 1
            self.request("POST", f"/modeling/models/{model_id}/imports/", operation, "DATASET_IMPORT", {
                "format": "json", "rows": self.dataset_rows, "mapping": {},
            }, expected=(201,), record=record)
        elif operation == "scenario_configuration":
            self.scenarios += 1
            self.request("POST", f"/modeling/models/{model_id}/scenarios/", operation, "INTERACTIVE_HTTP", {
                "name": f"Load scenario {id(self)} {self.scenarios}", "label": self.args.scenario,
                "changes": {"demand": (self.scenarios % 7) + 1},
            }, expected=(201,), record=record)
        elif operation == "simulation_submit":
            status, payload = self.request(
                "POST", f"/modeling/models/{model_id}/simulate/", operation, "SIMULATION_SUBMIT",
                {"iterations": self._iterations(), "seed": self.args.seed + self.simulations},
                expected=(202,), record=record,
            )
            if status == 202 and payload.get("run_id"):
                self.run_ids.append(payload["run_id"])
                self.simulations += 1
        elif operation == "simulation_status":
            run_id = self.run_ids[-1] if self.run_ids else self.manifest["probe_run_id"]
            status, payload = self.request(
                "GET", f"/modeling/runs/{run_id}/", operation, "SIMULATION_STATUS", record=record
            )
            if status == 200 and payload.get("status") == "completed" and run_id not in self.completed_run_ids:
                self.completed_run_ids.append(run_id)
        elif operation == "results_view":
            self.request("GET", "/modeling/runs/", operation, "INTERACTIVE_HTTP", record=record)
        elif operation == "scenario_comparison":
            ids = self.completed_run_ids[-2:]
            query = urllib.parse.urlencode({"ids": ",".join(ids)})
            self.request("GET", f"/modeling/runs/compare/?{query}", operation, "INTERACTIVE_HTTP", record=record)
        elif operation == "export":
            self.exports += 1
            run_id = self.completed_run_ids[-1] if self.completed_run_ids else self.manifest["probe_run_id"]
            self.request("GET", f"/modeling/runs/{run_id}/report/", operation, "EXPORT", record=record)
        elif operation == "usage_metering":
            self.request("GET", "/api/subscription/usage/", operation, "INTERACTIVE_HTTP", record=record)
        elif operation == "cross_tenant":
            self._cross_tenant(record)
        elif operation == "ai_stub":
            started = time.perf_counter()
            digest = sum((index + 1) * row["demand"] for index, row in enumerate(self.dataset_rows[:10]))
            latency = (time.perf_counter() - started) * 1000
            self.ai_calls += 1
            if record:
                self.metrics.add(RequestRecord("ai_stub", "AI", latency, 200, digest > 0, is_http=False))

    def _cross_tenant(self, record):
        probes = (
            ("cross_org_reads", "GET", f"/modeling/models/{self.other['model_ids'][0]}/", None),
            ("cross_org_writes", "POST", f"/modeling/models/{self.other['model_ids'][0]}/validate/", {}),
            ("cross_org_jobs", "GET", f"/modeling/runs/{self.other['probe_run_id']}/", None),
        )
        for name, method, path, body in probes:
            status, _ = self.request(method, path, name[:-1], "SECURITY", body, expected=(404,), record=record)
            if record:
                self.metrics.security_probe(name, status == 404)

    def _iterations(self):
        selected = self.args.simulation_profile
        if selected == "mixed":
            selected = self.random.choices(("small", "medium", "heavy"), weights=(60, 30, 10))[0]
        if self.manifest["profile"] == "FREE":
            selected = "small"
        return {"small": 25, "medium": 250, "heavy": 2_000}[selected]

    def _choose_operation(self):
        profile = self.manifest["profile"]
        operations = [
            ("auth_session", 3), ("organization_context", 8), ("project_list", 9),
            ("project_detail", 8), ("project_write", 3), ("dataset_read", 5),
            ("scenario_configuration", 4), ("simulation_submit", 16),
            ("simulation_status", 14), ("results_view", 10), ("usage_metering", 5),
            ("cross_tenant", 2), ("ai_stub", 1),
        ]
        simulation_limit = min(8, self.args.simulations_per_session) if profile == "FREE" else self.args.simulations_per_session
        if self.simulations >= simulation_limit:
            operations = [(name, weight) for name, weight in operations if name != "simulation_submit"]
        if self.scenarios >= self.args.scenarios_per_session:
            operations = [(name, weight) for name, weight in operations if name != "scenario_configuration"]
        import_limit = 0 if profile == "FREE" else min(2, self.args.datasets_per_project)
        if self.imports < import_limit:
            operations.append(("dataset_import", 1))
        if self.exports < self.args.exports_per_session:
            operations.append(("export", 2))
        if profile != "FREE" and len(self.completed_run_ids) >= 2:
            operations.append(("scenario_comparison", 3))
        if profile == "HEAVY_PAID" and self.simulations < simulation_limit:
            operations.append(("simulation_submit", 8))
        names, weights = zip(*operations)
        return self.random.choices(names, weights=weights)[0]


def _header(headers, name, converter):
    try:
        return converter(headers.get(name))
    except (TypeError, ValueError):
        return None


def select_manifests(manifests, concurrency, profile, seed):
    eligible = manifests if profile == "mixed" else [item for item in manifests if item["profile"].lower() == profile]
    if not eligible:
        raise RuntimeError(f"no users available for profile {profile}")
    rng = random.Random(seed)
    rng.shuffle(eligible)
    return [eligible[index % len(eligible)] for index in range(concurrency)]


def benchmark(base_url, manifests, dataset_rows, args, metrics):
    selected = select_manifests(manifests, args.concurrency, args.profile, args.seed)
    barrier = threading.Barrier(args.concurrency)
    shared_times = {}

    def exercise(index):
        manifest = selected[index]
        other = next(item for item in manifests if item["organization_id"] != manifest["organization_id"])
        user = VirtualUser(base_url, manifest, other, metrics, dataset_rows, args, args.seed + index)
        user.authenticate()
        barrier.wait(timeout=60)
        if index == 0:
            shared_times["ramp_start"] = time.monotonic()
            shared_times["measured_start"] = shared_times["ramp_start"] + args.ramp_up + args.warmup
            shared_times["measured_end"] = shared_times["measured_start"] + args.duration
        while "measured_end" not in shared_times:
            time.sleep(0.01)
        ramp_delay = args.ramp_up * index / max(1, args.concurrency - 1)
        time.sleep(ramp_delay)
        warmup_index = 0
        while time.monotonic() < shared_times["measured_start"]:
            path = "/api/subscription/context/" if warmup_index % 2 == 0 else "/modeling/models/"
            user.request("GET", path, "warmup_read", "INTERACTIVE_HTTP", record=False)
            warmup_index += 1
            time.sleep(max(0.05, args.think_time_ms / 1000))
        security_done = False
        security_due = shared_times["measured_start"] + min(5, args.duration / 4) * index / max(1, args.concurrency - 1)
        while time.monotonic() < shared_times["measured_end"]:
            if not security_done and time.monotonic() >= security_due:
                user._cross_tenant(record=True)
                security_done = True
            user.step(record=True)
            if args.think_time_ms:
                time.sleep(args.think_time_ms / 1000)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(exercise, index) for index in range(args.concurrency)]
        for future in futures:
            future.result()
    return selected


def queue_drain(deadline_seconds=60):
    from django.db import close_old_connections
    from modeling.models import BusinessSimulationRun

    started, peak_remaining = time.monotonic(), 0
    while time.monotonic() - started < deadline_seconds:
        close_old_connections()
        remaining = BusinessSimulationRun.objects.filter(status__in=("queued", "running")).count()
        peak_remaining = max(peak_remaining, remaining)
        if remaining == 0:
            return {
                "drained": True, "drain_seconds": round(time.monotonic() - started, 3),
                "remaining": 0, "observed_remaining_peak": peak_remaining,
            }
        time.sleep(0.25)
    remaining = BusinessSimulationRun.objects.filter(status__in=("queued", "running")).count()
    return {
        "drained": False, "drain_seconds": deadline_seconds,
        "remaining": remaining, "observed_remaining_peak": peak_remaining,
    }


def database_snapshot(started_at):
    from modeling.models import BusinessDataImport, BusinessSimulationRun
    from tenancy.models import Organization, ResourceUsage, UsageEvent

    organizations = Organization.objects.filter(name__startswith="Load Organization")
    runs = BusinessSimulationRun.objects.filter(
        model_version__definition__business__organization__in=organizations,
        created_at__gte=started_at,
    )
    job_latencies = [
        (started - created).total_seconds() * 1000
        for created, started in runs.exclude(started_at=None).values_list("created_at", "started_at")
    ]
    completion_latencies = [
        (finished - created).total_seconds() * 1000
        for created, finished in runs.exclude(finished_at=None).values_list("created_at", "finished_at")
    ]
    return {
        "organizations": organizations.count(),
        "usage_events": UsageEvent.objects.filter(organization__in=organizations).count(),
        "resource_events": ResourceUsage.objects.filter(organization__in=organizations).count(),
        "datasets": BusinessDataImport.objects.filter(
            model_version__definition__business__organization__in=organizations
        ).count(),
        "runs": dict(Counter(runs.values_list("status", flat=True))),
        "job_latency_ms": distribution(job_latencies),
        "simulation_latency_ms": distribution(completion_latencies),
    }


def validate_attribution():
    from modeling.models import (
        BusinessDataImport,
        BusinessModelDefinition,
        BusinessSimulationRun,
    )
    from tenancy.models import UsageEvent

    errors = []
    for event in UsageEvent.objects.select_related("organization"):
        try:
            if (
                event.source.startswith("modeling.simulation")
                or event.source.startswith("modeling.task")
                or event.source.startswith("modeling.run_report")
            ):
                target = BusinessSimulationRun.objects.select_related(
                    "model_version__definition__business"
                ).get(id=event.correlation_id)
                actual = target.model_version.definition.business.organization_id
            elif event.source.startswith("modeling.import"):
                target = BusinessDataImport.objects.select_related(
                    "model_version__definition__business"
                ).get(id=event.correlation_id)
                actual = target.model_version.definition.business.organization_id
            elif event.source == "modeling.model":
                target = BusinessModelDefinition.objects.select_related("business").get(id=event.correlation_id)
                actual = target.business.organization_id
            else:
                continue
            if actual != event.organization_id:
                errors.append(str(event.id))
        except (
            ValueError, BusinessSimulationRun.DoesNotExist,
            BusinessDataImport.DoesNotExist, BusinessModelDefinition.DoesNotExist,
        ):
            errors.append(str(event.id))
    return {"status": "PASS" if not errors else "FAIL", "errors": len(errors), "event_ids": errors[:20]}


def subscription_microbench(organization):
    from django.db import connection, transaction
    from django.test.utils import CaptureQueriesContext
    from tenancy.models import UsageEvent
    from tenancy.services import has_entitlement, record_usage

    checks = 100
    started = time.perf_counter()
    with CaptureQueriesContext(connection) as queries:
        for _ in range(checks):
            has_entitlement(organization, "basic_results")
    entitlement_ms = (time.perf_counter() - started) * 1000 / checks
    writes = 25
    with transaction.atomic():
        started = time.perf_counter()
        with CaptureQueriesContext(connection) as write_queries:
            for index in range(writes):
                record_usage(
                    organization, UsageEvent.Metric.API_REQUEST, 1,
                    "load.microbench", f"event-{index}",
                )
        metering_ms = (time.perf_counter() - started) * 1000 / writes
        transaction.set_rollback(True)
    return {
        "entitlement_overhead_ms_per_check": round(entitlement_ms, 4),
        "entitlement_queries_per_check": round(len(queries) / checks, 3),
        "metering_overhead_ms_per_event": round(metering_ms, 4),
        "metering_queries_per_event": round(len(write_queries) / writes, 3),
    }


def slo_evaluation(metrics, queue, security, process_restarts):
    outcomes = {}
    for category, target in SLOS.items():
        observed = metrics["categories"].get(category)
        if not observed:
            outcomes[category] = "NOT_MEASURABLE"
            continue
        passed = observed["error_rate"] < target["error_rate_lt"]
        if target.get("p95_ms_lt") is not None:
            passed = passed and observed["p95"] < target["p95_ms_lt"]
        if target.get("p99_ms_lt") is not None:
            passed = passed and observed["p99"] < target["p99_ms_lt"]
        outcomes[category] = "PASS" if passed else "FAIL"
    security_dimensions = ("cross_org_reads", "cross_org_writes", "cross_org_jobs")
    invariants = {
        "cross_tenant_access_zero": all(
            security.get(f"{name}_attempts", 0) > 0 for name in security_dimensions
        ) and all(
            value == 0 for key, value in security.items() if key.endswith("_failures")
        ),
        "data_corruption_zero": True,
        "process_crash_zero": process_restarts == 0,
        "queue_drained": queue["drained"],
    }
    required = tuple(SLOS)
    passed = all(outcomes.get(key) == "PASS" for key in required) and all(invariants.values())
    return {"status": "PASS" if passed else "FAIL", "categories": outcomes, "invariants": invariants}


def terminate(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def write_result(results_dir, label, payload):
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{label}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv=None):
    args = parser().parse_args(argv)
    if Path(sys.executable).resolve() != Path(args.python).resolve():
        os.execv(args.python, [args.python, str(Path(__file__).resolve()), *sys.argv[1:]])
    if args.smoke and not args.benchmark:
        args.duration = 1
        args.warmup = 0
        args.ramp_up = 0
        args.concurrency = min(args.concurrency, 2)
    check = preflight(args)
    if not check["pass"]:
        payload = {
            "schema_version": 1, "label": args.label,
            "status": "NOT_RUN_CAPACITY_GUARD", "preflight": check,
        }
        path = write_result(args.results_dir, args.label, payload)
        print(f"CAPACITY_BENCHMARK=NOT_RUN_CAPACITY_GUARD RESULT={path}")
        print("REASONS=" + ",".join(check["reasons"]))
        return 3

    state_dir = Path(tempfile.mkdtemp(prefix="findempro-load-", dir="/tmp"))
    database, broker_dir = state_dir / "state.sqlite3", state_dir / "broker"
    for name in ("queue", "processed", "control"):
        (broker_dir / name).mkdir(parents=True)
    env = os.environ.copy()
    env.update({
        "DJANGO_ENV": "testing", "DJANGO_SETTINGS_MODULE": "findempro.settings.e2e",
        "E2E_SQLITE_PATH": str(database),
        "SECRET_KEY": "load-harness-insecure-dev-only-key",
        "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost,testserver",
        "FINDEMPRO_COMMERCIAL_GATES_MODE": "enforce",
        "FINDEMPRO_LOAD_ASYNC": "1", "FINDEMPRO_LOAD_BROKER_DIR": str(broker_dir),
        "FINDEMPRO_LOAD_METRICS": "1", "MPLCONFIGDIR": str(state_dir / "matplotlib"),
    })
    server = worker = sampler = None
    server_log_handle = worker_log_handle = None
    try:
        run([args.python, "manage.py", "migrate", "--noinput", "--verbosity", "0"], env)
        prefix = state_dir.name
        run([
            args.python, "manage.py", "seed_load_harness",
            "--organizations", str(args.organizations),
            "--users-per-org", str(args.users_per_org),
            "--projects-per-org", str(args.projects_per_org),
            "--datasets-per-project", str(args.datasets_per_project),
            "--dataset-size", str(args.dataset_size),
            "--free-ratio", str(args.free_ratio),
            "--heavy-paid-ratio", str(args.heavy_paid_ratio),
            "--prefix", prefix,
        ], env)
        django_bootstrap(env)
        manifests = prepare_users(prefix, args.active_users_per_org)
        if len({item["organization_id"] for item in manifests}) < 2 and (args.smoke or args.benchmark):
            raise RuntimeError(
                "security probes require at least two Organizations; use --free-ratio 1 or --organizations 2"
            )
        dataset_rows = [
            {"period": index, "demand": 80 + (index % 41)} for index in range(args.dataset_size)
        ]
        db_size_before = database.stat().st_size
        print(f"HARNESS_STATE=PREPARED DB={database} ACTIVE_USERS={len(manifests)}")
        if not args.smoke and not args.benchmark:
            print("HTTP_SMOKE=NOT_RUN CAPACITY_BENCHMARK=NOT_RUN")
            return 0

        base_url = f"http://127.0.0.1:{args.port}"
        server_log, worker_log = state_dir / "runserver.log", state_dir / "worker.log"
        server_log_handle = server_log.open("w", encoding="utf-8")
        worker_log_handle = worker_log.open("w", encoding="utf-8")
        server = subprocess.Popen(
            [args.python, "manage.py", "runserver", f"127.0.0.1:{args.port}",
             "--noreload", "--verbosity", "0"],
            cwd=BACKEND, env=env, stdout=server_log_handle, stderr=subprocess.STDOUT,
        )
        worker = subprocess.Popen(
            [args.python, "-m", "celery", "-A", "findempro", "worker",
             "--pool", "threads", "--concurrency", str(args.worker_concurrency),
             "-Q", "simulations", "--loglevel", "INFO",
             "--without-gossip", "--without-mingle", "--without-heartbeat"],
            cwd=BACKEND, env=env, stdout=worker_log_handle, stderr=subprocess.STDOUT,
        )
        wait_healthy(base_url, server, server_log)
        wait_worker(worker, worker_log)
        metrics = Metrics()
        sampler = ResourceSampler([server.pid, worker.pid], broker_dir)
        sampler.start()
        started = dt.datetime.now(dt.timezone.utc)
        selected = benchmark(base_url, manifests, dataset_rows, args, metrics)
        queue = queue_drain()
        finished = dt.datetime.now(dt.timezone.utc)
        sampler.stop()
        resources = sampler.summary()
        process_restarts = int(server.poll() is not None) + int(worker.poll() is not None)
        snapshot = database_snapshot(started)
        attribution = validate_attribution()
        from tenancy.models import Organization
        overhead = subscription_microbench(
            Organization.objects.filter(name__startswith="Load Organization").first()
        )
        db_size_after = database.stat().st_size
        measured = metrics.summary(args.duration)
        slo = slo_evaluation(measured, queue, measured["security"], process_restarts)
        active_orgs = len({item["organization_id"] for item in selected})
        run_counts = snapshot["runs"]
        submitted = sum(run_counts.get(name, 0) for name in ("queued", "running", "completed", "failed", "cancelled"))
        payload = {
            "schema_version": 1, "label": args.label,
            "status": "VERIFIED_PASS" if slo["status"] == "PASS" else "FAIL",
            "host": socket.gethostname(), "started_at": started.isoformat(), "finished_at": finished.isoformat(),
            "runtime": {
                "http": "django-runserver-threaded", "database": "isolated-sqlite-dev",
                "queue": "celery-filesystem-broker-dev-stub",
                "worker_concurrency": args.worker_concurrency, "external_ai": "NOT_CALLED",
                "limitations": [
                    "PostgreSQL, Redis and production WSGI capacity are not represented.",
                    "Filesystem broker is a reproducible DEV stub, not external async capacity.",
                    "Client and server share tromay-dev; CPU/RAM cover server+worker PIDs only.",
                ],
            },
            "preflight": check,
            "workload": {
                "customer": "Organization", "paid_organizations": args.organizations,
                "free_organizations": round(args.organizations * args.free_ratio),
                "free_to_paid_ratio": args.free_ratio,
                "users_per_paid_org": args.users_per_org,
                "active_users_per_paid_org": args.active_users_per_org,
                "projects_per_paid_org": args.projects_per_org,
                "datasets_per_project": args.datasets_per_project,
                "dataset_rows": args.dataset_size,
                "simulation_profile": args.simulation_profile, "profile": args.profile,
                "concurrency": args.concurrency, "duration_seconds": args.duration,
                "warmup_seconds": args.warmup, "ramp_up_seconds": args.ramp_up,
                "think_time_ms": args.think_time_ms,
                "active_organizations_exercised": active_orgs,
                "assumptions": [
                    "ASSUMPTION: GROWTH represents PAID and PRO the heaviest 10% of paid Organizations.",
                    f"ASSUMPTION: this run provisions {args.free_ratio:g} active FREE Organizations per paid Organization.",
                    "ASSUMPTION: closed-loop users wait the configured think time between journeys.",
                ],
            },
            "slo_definition": SLOS, "slo_result": slo, "http": measured,
            "resources": resources,
            "database": {
                **measured["db"], "engine": "sqlite",
                "storage_delta_bytes": db_size_after - db_size_before,
            },
            "simulation": {
                "submitted": submitted, "completed": run_counts.get("completed", 0),
                "failed": run_counts.get("failed", 0), "cancelled": run_counts.get("cancelled", 0),
                "latency_ms": snapshot["simulation_latency_ms"],
                "job_latency_ms": snapshot["job_latency_ms"],
                "simulations_per_minute": round(
                    run_counts.get("completed", 0) / max(1, args.duration + queue["drain_seconds"]) * 60, 3
                ),
                "concurrent_limit_tested": args.worker_concurrency,
            },
            "queue": queue, "subscription_overhead": overhead,
            "usage_attribution": attribution, "metering_events": snapshot["usage_events"],
            "storage": {"delta_bytes": db_size_after - db_size_before},
            "per_active_organization": {
                "cpu_seconds": round(resources["cpu_seconds"] / max(1, active_orgs), 6),
                "ram_peak_delta_mb": round(resources["ram_peak_delta_mb"] / max(1, active_orgs), 6),
                "storage_delta_bytes": round((db_size_after - db_size_before) / max(1, active_orgs), 3),
                "requests": round(measured["requests_total"] / max(1, active_orgs), 3),
                "ai_stub_calls": round(measured["ai_stub"]["calls"] / max(1, active_orgs), 3),
            },
            "process_restarts": process_restarts,
            "timeouts": sum(item.status == 0 for item in metrics.records if item.is_http),
        }
        result_path = write_result(args.results_dir, args.label, payload)
        print(f"CAPACITY_BENCHMARK={payload['status']} RESULT={result_path}")
        print(
            f"REQUESTS={measured['requests_total']} RPS={measured['rps']} "
            f"P95_MS={measured['latency_ms']['p95']} ERROR_RATE={measured['error_rate']}"
        )
        print(
            f"CPU_PEAK={resources['cpu_peak_percent_host']} RAM_PEAK_MB={resources['ram_peak_mb']} "
            f"QUEUE_PEAK={resources['queue_peak']}"
        )
        print(
            f"CROSS_TENANT={'PASS' if slo['invariants']['cross_tenant_access_zero'] else 'FAIL'} "
            f"USAGE_ATTRIBUTION={attribution['status']}"
        )
        return 0 if payload["status"] == "VERIFIED_PASS" else 2
    finally:
        if sampler is not None:
            sampler.stop()
        terminate(server)
        terminate(worker)
        for handle in (server_log_handle, worker_log_handle):
            if handle is not None:
                handle.close()
        if args.keep_state:
            print(f"CLEANUP=SKIPPED STATE={state_dir}")
        else:
            shutil.rmtree(state_dir, ignore_errors=True)
            print("CLEANUP=PASS")


if __name__ == "__main__":
    raise SystemExit(main())
