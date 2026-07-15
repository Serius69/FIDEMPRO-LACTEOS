# FindemproAI — Aceleración del Monte Carlo (GPU/CPU) y despliegue

Sesión 2026-07-08. Motor de simulación **vectorizado** con backend seleccionable
**CuPy (GPU) / NumPy (CPU) y fallback automático**.

## Qué cambió

El motor Monte Carlo ejecutaba un bucle Python `for período: for escenario:
engine.run_period(...)` — hasta millones de iteraciones objeto-por-objeto. Como
cada escenario corre *stateless* (`reset_state()` antes de cada uno), la grilla
T×N es independiente y se puede evaluar con **operaciones de array**.

Nuevos módulos:

| Archivo | Rol |
|---|---|
| `simulate/core/gpu_backend.py` | Selección de backend (CuPy/NumPy), detección segura de GPU, fallback, namespace matemático vectorizado. |
| `simulate/core/vectorized_engine.py` | Motor vectorizado: evalúa las MISMAS ecuaciones con variables array-valuadas. `can_vectorize()` valida equivalencia contra el motor escalar antes de usarlo. |
| `simulate/services/simulation_service.py` | `run_full_pipeline()` usa el motor vectorizado con fallback al escalar. |
| `simulate/tests/test_vectorized_engine.py` | Equivalencia numérica + backend + distribuciones. |

**Equivalencia numérica: exacta** por celda (validado). Si un modelo de ecuaciones
no es vectorizable (construcciones no aritméticas, división por cero, etc.),
`can_vectorize()` devuelve `False` y el pipeline cae al motor escalar clásico.

## Rendimiento (RTX 5070 Ti, warm)

| Escenarios (T=30) | Bucle escalar actual | Vectorizado CPU | Vectorizado GPU |
|---|---|---|---|
| N=2.000  | ~6.220 ms | ~3 ms | ~3 ms |
| N=100.000 | (min.) | ~176 ms | ~48 ms (agregación en GPU) |
| N=500.000 | (inviable) | ~955 ms | ~248 ms |

- **Vectorización** = el win dominante: **~1.000–2.000×** sobre el bucle actual.
  Funciona en CPU y **se despliega al cluster K8s sin dependencias nuevas**.
- **GPU (CuPy)** = ~3× adicional end-to-end (hasta ~70× en cómputo puro), crece con N.

## Flags de entorno

| Variable | Valores | Default | Efecto |
|---|---|---|---|
| `FINDEMPRO_MC_ENGINE` | `vectorized` \| `scalar` | `vectorized` | Motor Monte Carlo. `scalar` fuerza el bucle clásico. |
| `FINDEMPRO_GPU` | `auto` \| `on` \| `off` | `auto` | Backend. `auto`=GPU si CuPy compila kernels; `off`=NumPy siempre. |

En el cluster K8s CPU no hace falta configurar nada: sin CuPy, `auto` cae a NumPy
y se obtiene igualmente el gran salto de la vectorización.

---

## Despliegue A — Producción CPU (cluster K8s) — RECOMENDADO

El código nuevo **no agrega dependencias** para CPU (usa numpy, ya presente).
Solo hay que reconstruir la imagen y hacer rollout con el tag nuevo `v20260708`
(ya referenciado en `infra/k8s/public/findemproai/*.yaml`).

> ⚠️ Regla del ecosistema: **nunca `docker push`**. Build + `docker save | ctr import`
> en el worker K8s. Ejecutar en **Windows/Docker Desktop** (esta sesión Linux no
> tiene acceso al cluster).

> ⚠️ **Verificar el namespace antes del apply.** Los manifests declaran
> `namespace: public`, pero el CLAUDE.md del ecosistema ubica `findemproai` en
> `private`. Comprobar dónde corre realmente:
> ```powershell
> kubectl get deploy -A | Select-String findempro
> ```
> Si está en `private`, ajustar `metadata.namespace` en los YAML (o usar
> `kubectl apply -n private -f ...` tras quitar el campo) ANTES de aplicar,
> para no crear un despliegue duplicado en el namespace equivocado.

```powershell
# desde findempro/
docker build -t kapitalya/findemproai:v20260708 .
docker save kapitalya/findemproai:v20260708 -o findemproai.tar
docker exec -i desktop-worker4 ctr images import - < findemproai.tar
Remove-Item findemproai.tar

# rollout (los manifests ya apuntan a v20260708, imagePullPolicy: IfNotPresent)
kubectl apply -f infra/k8s/public/findemproai/
kubectl rollout status deploy/findemproai -n public
kubectl rollout status deploy/findemproai-celery-worker -n public
```

Verificación:
```powershell
kubectl logs -n public deploy/findemproai-celery-worker | Select-String "MC vectorizado"
# → "Pipeline MC vectorizado [numpy/cpu]: 30×1000 celdas en 0.0XXs"
```

## Despliegue B — Worker GPU (host Linux con RTX 5070 Ti) — OPCIONAL

El cluster K8s (Docker Desktop/Windows) **no expone GPU**. Para ejercitar la GPU
de verdad se corre un worker Celery dedicado a la cola `simulations` en un host
Linux con GPU, apuntando al mismo broker Redis. Requiere driver NVIDIA +
`nvidia-container-toolkit`.

```bash
# desde findempro/ en el host Linux con GPU
docker compose -f docker-compose.prod.yml -f docker-compose.gpu.yml up -d --build

# comprobar que tomó la GPU
docker compose -f docker-compose.prod.yml -f docker-compose.gpu.yml \
  exec findempro_celery_gpu python -c \
  "from simulate.core import gpu_backend as g; print(g.backend_name())"
# → cupy/gpu
```

`docker-compose.gpu.yml` mueve la cola `simulations` al worker GPU y deja el
worker CPU solo con `default`. Imagen: `Dockerfile.gpu` (usa wheels pip
`nvidia-cuda-*-cu12`, sin imagen base CUDA).

### Nota Blackwell (RTX 50xx / sm_120)
CuPy necesita **NVRTC ≥ 12.8** para compilar kernels en Blackwell; con 12.4 falla
con `CUDA_ERROR_NO_BINARY_FOR_GPU`. `requirements/gpu.txt` fija
`nvidia-cuda-nvrtc-cu12>=12.8` y `Dockerfile.gpu` ajusta `LD_LIBRARY_PATH` para
que CuPy use ese NVRTC. Ya validado en la 5070 Ti (CuPy 13.6.0 + NVRTC 12.9).
