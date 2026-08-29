#!/usr/bin/env python3
"""No-Docker DEV harness. Prepares data by default; never runs a large benchmark implicitly."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "findempro"
DIRECT_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def positive(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def ratio(value):
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--organizations", type=positive, default=1)
    result.add_argument("--users-per-org", type=positive, default=1)
    result.add_argument("--concurrency", type=positive, default=1)
    result.add_argument("--projects-per-org", type=positive, default=1)
    result.add_argument("--simulations-per-session", type=positive, default=1)
    result.add_argument("--dataset-size", type=positive, default=100)
    result.add_argument("--free-ratio", type=ratio, default=1.0)
    result.add_argument("--duration", type=positive, default=5)
    result.add_argument("--port", type=positive, default=58177)
    result.add_argument("--python", default=sys.executable)
    result.add_argument("--smoke", action="store_true", help="start HTTP runtime and execute a bounded smoke")
    result.add_argument("--keep-state", action="store_true")
    return result


def run(command, env):
    subprocess.run(command, cwd=BACKEND, env=env, check=True)


def request_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    # The harness is loopback-only. Never inherit host/sandbox HTTP proxies.
    with DIRECT_OPENER.open(request, timeout=timeout) as response:
        return response.status, json.loads(response.read() or b"{}")


def wait_healthy(base_url, server=None, log_path=None, deadline_seconds=90):
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        try:
            status, _ = request_json(f"{base_url}/health/live/", timeout=2)
            if status == 200:
                return
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            if server is not None and server.poll() is not None:
                detail = log_path.read_text(errors="replace")[-4000:] if log_path and log_path.exists() else ""
                raise RuntimeError(
                    f"backend exited before health (code={server.returncode})\n{detail}"
                )
            time.sleep(0.2)
    detail = log_path.read_text(errors="replace")[-4000:] if log_path and log_path.exists() else ""
    raise RuntimeError(f"backend did not become healthy\n{detail}")


def smoke_once(base_url, dataset_size):
    demand = max(1, dataset_size)
    return request_json(f"{base_url}/api/simulate/montecarlo/", {
        "ventas_mes": demand * 100,
        "gastos_fijos": demand * 40,
        "tiempo_operando": 12,
        "tipo_negocio": "generic",
        "horizonte": 3,
        "simulaciones": min(1000, max(100, dataset_size)),
    })[0]


def main(argv=None):
    args = parser().parse_args(argv)
    state_dir = Path(tempfile.mkdtemp(prefix="findempro-load-"))
    database = state_dir / "state.sqlite3"
    env = os.environ.copy()
    env.update({
        "DJANGO_ENV": "testing",
        "DJANGO_SETTINGS_MODULE": "findempro.settings.e2e",
        "E2E_SQLITE_PATH": str(database),
        "SECRET_KEY": "load-harness-insecure-dev-only-key",
        "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost,testserver",
        "FINDEMPRO_COMMERCIAL_GATES_MODE": "enforce",
        "MPLCONFIGDIR": str(state_dir / "matplotlib"),
    })
    server = None
    server_log = None
    try:
        run([args.python, "manage.py", "migrate", "--noinput"], env)
        run([
            args.python, "manage.py", "seed_load_harness",
            "--organizations", str(args.organizations),
            "--users-per-org", str(args.users_per_org),
            "--projects-per-org", str(args.projects_per_org),
            "--free-ratio", str(args.free_ratio),
            "--prefix", state_dir.name,
        ], env)
        print(f"HARNESS_STATE=PREPARED DB={database}")
        if not args.smoke:
            print("HTTP_SMOKE=NOT_RUN use --smoke; CAPACITY_BENCHMARK=NOT_RUN")
            return 0
        base_url = f"http://127.0.0.1:{args.port}"
        server_log = (state_dir / "runserver.log").open("w", encoding="utf-8")
        server = subprocess.Popen(
            [args.python, "manage.py", "runserver", f"127.0.0.1:{args.port}", "--noreload"],
            cwd=BACKEND, env=env, stdout=server_log, stderr=subprocess.STDOUT,
        )
        wait_healthy(base_url, server=server, log_path=state_dir / "runserver.log")
        operations = min(
            args.concurrency * args.simulations_per_session,
            args.concurrency * max(1, args.duration),
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            statuses = list(pool.map(
                lambda _index: smoke_once(base_url, args.dataset_size), range(operations)
            ))
        if any(status != 200 for status in statuses):
            raise RuntimeError(f"HTTP smoke failed: {statuses}")
        print(f"HTTP_SMOKE=PASS REQUESTS={len(statuses)} CONCURRENCY={args.concurrency}")
        print("CAPACITY_BENCHMARK=NOT_RUN")
        return 0
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        if server_log is not None:
            server_log.close()
        if args.keep_state:
            print(f"CLEANUP=SKIPPED STATE={state_dir}")
        else:
            shutil.rmtree(state_dir, ignore_errors=True)
            print("CLEANUP=PASS")


if __name__ == "__main__":
    raise SystemExit(main())
