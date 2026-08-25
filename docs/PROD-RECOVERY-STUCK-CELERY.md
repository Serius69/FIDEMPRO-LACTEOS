# PROD Recovery — 36 stuck Celery messages (findempro)

Procedure for PROD only, to run AFTER the routing fix (`fix/celery-queue-routing-20260825`)
is deployed there. Nothing here was executed against PROD from this DEV session — DEV has
no access to PROD's Redis. This is read-only reconnaissance guidance plus a decision table.

## Why this is needed

Before 2026-08-25's fix, every task with no explicit route landed in Celery's implicit
`celery` queue, which `findempro_celery` never consumed (`-Q default,simulations`). 36
messages accumulated in that list on PROD's `findempro_redis` (db0, the broker) before
this was caught (see `FINDING-celery-default-queue-mismatch-findempro.md`). Deploying the
fix does **not** touch existing queued messages — Redis lists aren't reprocessed
retroactively. The 36 stay in `celery` until someone moves or discards them.

## Step 1 — INSPECT (read-only, safe at any time)

```bash
docker exec findempro_redis redis-cli -n 0 LLEN celery      # should read 36 (or more, if it grew)
docker exec findempro_redis redis-cli -n 0 LRANGE celery 0 -1 > /tmp/stuck-celery-messages.json
```

Each element is a Celery/kombu JSON envelope. For each one, extract at minimum:

```bash
python3 - <<'PY'
import json
with open('/tmp/stuck-celery-messages.json') as f:
    raw = f.read()
# LRANGE output is redis-cli's own format; if using redis-cli --no-raw, parse per line.
# Prefer: redis-cli -n 0 --no-raw LRANGE celery 0 -1, then json.loads each unescaped line.
PY
```

(Adjust to how the messages were captured — the point is to decode `task`, `id`,
`args`/`kwargs`, and the envelope's `properties.reply_to`/timestamps for each entry, not to
touch the list yet.)

For every message, record:

| Field | Where it comes from |
|---|---|
| `task` | envelope `headers.task` (or top-level `task` in the older protocol) — this is the task NAME, e.g. `simulate.tasks.run_stateless_simulation` |
| `id` | envelope `headers.id` — the Celery task_id (matches what the frontend polled, if any) |
| `age` | derived from `headers.eta`/`headers.expires` if present, or from when the message was known to exist (2026-08-25 discovery predates all but 1) |
| `payload validity` | can `args`/`kwargs` still `json.loads` cleanly and match the current task signature? |

**Do not assume all 36 are `run_stateless_simulation`.** The finding doc confirmed only 1
of the 36 by task_id (this session's own test). The other 35 are unidentified until Step 1
is actually run against PROD. `execute_simulation_async`, `run_business_simulation`,
`run_sensitivity_async`, and `generate_report_pdf_async` all had live call sites in the app
(confirmed by grep against `main` during this DEV investigation) and were equally capable of
landing in the stuck `celery` queue — they are not ruled out.

## Step 2 — CLASSIFY

Group the 36 by `task` name from Step 1. For each group, apply the REQUEUE_SAFE verdict
below (established from reading the actual write paths in DEV, not assumed):

| Task | Side effects on success | REQUEUE_SAFE | Why |
|---|---|---|---|
| `simulate.tasks.run_stateless_simulation` | None — pure function, no DB writes, result only in Celery result backend | **YES** | Stateless by design (see its own docstring: "No persiste nada en BD"). Firing it now is wasted compute if the original requester's browser already gave up (frontend has its own 5-min client timeout — see Failure UX below), but it cannot corrupt anything. |
| `simulate.tasks.execute_simulation_async` | Writes `ResultSimulation` rows via `SimulationService.run_and_save` | **YES** | `save_pipeline_results_to_db` is explicitly idempotent by design: "borra registros previos de la simulación antes de insertar" (delete-then-bulk_create). Re-running for the same `simulation_id` cannot duplicate rows. |
| `modeling.run_business_simulation` | Updates a single `BusinessSimulationRun` row via a guarded `.filter(status="running").update(...)` | **YES** | Guarded update means a second execution against an already-completed run is a no-op (`updated=0` → returns `{"status": "cancelled", ...}`). Safe even if requeued twice. |
| `report.tasks.generate_report_pdf_async` / `generate_simulation_pdf_async` | Overwrites a cache key (`pdf_bytes:*`, TTL 1h) | **YES** | Cache `.set()` on a deterministic key — re-running just overwrites the same key. **Note:** `generate_simulation_pdf_async` has no live call site anywhere in `main` — if any stuck message names it, that itself is worth flagging as dead code triggered from somewhere unexpected. |
| `simulate.tasks.run_sensitivity_async` | Writes a cache key (`sensitivity:{project_id}:{task_id}`) | **YES** | Keyed by the *new* task_id at execution time — never collides with a prior run. No stale-data risk beyond the cache TTL (1h). |
| `simulate.tasks.send_simulation_complete_email` / `simulate.tasks.check_var_alerts_async` | Sends real email to a real user | **CONDITIONAL** | Not data-unsafe, but firing a "your simulation is done" or risk-alert email for a simulation the user ran hours/days ago is a stale, confusing notification. Recommend **DISCARD**, not requeue, for these two if any are found among the 36 — the underlying simulation itself should be re-run via its (idempotent) parent task instead of just re-sending the email artifact of a run whose numbers may already be irrelevant. |
| `simulate.tasks.cleanup_old_simulations` / `daily_statistics_update` | Maintenance/read-mostly | **YES** | No user-visible side effect from a delayed run. Also: neither is actually registered in `django_celery_beat`'s `PeriodicTask` table in this codebase despite the "configure in celery beat" comment — they are not scheduled today regardless of this incident. |
| `findempro.celery.debug_task` | None (diagnostic no-op) | **YES** | Trivial. |

## Step 3 — REQUEUE_SAFE / DISCARD_INVALID decision, by message

For each of the 36, after classifying by task:

1. If `payload validity` failed (args no longer deserialize against the current task
   signature — e.g. an old `execute_simulation_async(simulation_id)` where that
   `simulation_id` was since deleted) → **DISCARD_INVALID**.
2. If the task is `send_simulation_complete_email` / `check_var_alerts_async` → **DISCARD**
   per the CONDITIONAL row above (re-run the parent simulation task instead, if desired).
3. Otherwise → **REQUEUE_SAFE=YES** per the table. Requeue by re-publishing to the queue the
   fixed `CELERY_TASK_ROUTES` now assigns that task name to (`default` or `simulations`),
   NOT back into `celery`:

   ```bash
   # For each message payload extracted in Step 1, re-publish through the app's own
   # routing (do NOT hand-craft the Redis LPUSH — let Celery's amqp router pick the
   # queue the fixed settings now assign):
   docker exec findempro_backend python manage.py shell -c "
   from celery import Celery
   app = Celery('findempro'); app.config_from_object('django.conf:settings', namespace='CELERY')
   app.send_task('<task-name-from-step-1>', args=[...], kwargs={...})
   "
   ```

4. Once every message has been re-published or discarded, drain the original stuck list
   (only after confirming nothing worth keeping remains in it):

   ```bash
   docker exec findempro_redis redis-cli -n 0 DEL celery
   ```

   Do this LAST, after Step 3 is fully done for all 36 — `DEL` is irreversible.

## Step 4 — verify no new backlog

```bash
docker exec findempro_redis redis-cli -n 0 LLEN celery       # expect 0 going forward
docker exec findempro_redis redis-cli -n 0 LLEN default
docker exec findempro_redis redis-cli -n 0 LLEN simulations
docker exec findempro_celery celery -A findempro inspect active
docker exec findempro_celery celery -A findempro inspect reserved
```

Add a synthetic check (per the finding doc's own recommendation, not newly invented here):
alert if `LLEN celery` on the broker db is nonzero for more than a few minutes — that queue
should be permanently empty under the fixed routing, so any growth again means a new task
was added without a route.
