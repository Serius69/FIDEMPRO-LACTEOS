# Harness DEV no-Docker y preparación de carga

El harness canónico es `scripts/load/findempro_load_harness.py`. Solo usa estado SQLite temporal,
loopback y el Python explícito; no conoce hosts/credenciales de PROD, Redis ni Docker.

Preparación (no ejecuta benchmark):

```bash
./scripts/load/findempro_load_harness.py \
  --python /home/sergui/dev/venvs/findempro-py312/bin/python \
  --organizations 2 --users-per-org 2 --projects-per-org 1 \
  --concurrency 2 --simulations-per-session 1 --dataset-size 100 \
  --free-ratio 0.5 --duration 10
```

Smoke HTTP local acotado:

```bash
./scripts/load/findempro_load_harness.py \
  --python /home/sergui/dev/venvs/findempro-py312/bin/python --smoke
```

El command `seed_load_harness` crea Organizations, memberships, subscriptions y proyectos
deterministas en la DB aislada. El script migra/seed, puede arrancar runserver en
`127.0.0.1:58177`, valida health y ejecuta un workload público Monte Carlo pequeño; luego limpia
server y directorio temporal salvo `--keep-state`.

Evidencia DEV 2026-08-29: prepare PASS con 2 Organizations, 4 usuarios y 2 proyectos; smoke
HTTP PASS con 2 requests a concurrency 2; ambos ejecutaron migrations y cleanup. El cliente
loopback ignora deliberadamente proxies del host/sandbox.

Parámetros preparados para el ciclo siguiente: Organizations, users/org, concurrency,
projects/org, simulations/session, dataset size, free ratio y duration. Este ciclo no declara
`LOAD_READY` ni ejecuta S1=25, S2=100, S3=500 o S4=1000.
