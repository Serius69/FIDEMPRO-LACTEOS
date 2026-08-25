# Handoff a PROD — findempro-app, release f88196d2

**Estado:** listo para que un operador de PROD lo tome. **No desplegado desde DEV.**
PROD corre en el host `tromay`; este host (`tromay-dev`) no tiene acceso ni debe tenerlo.

---

## 1. Identidad exacta de lo que se despliega

| | |
|---|---|
| Commit publicado | `f88196d2db52ecf12fdbe257ada4b2fa15f9c536` |
| Rama | `main` (SHA remoto verificado por `ls-remote` y por la API) |
| SHA base en PROD | `40013c22beafbbd1589024c08242a82ba545ab9a` |
| Run de release | [`32806805314`](https://github.com/Serius69/FindemproAI/actions/runs/32806805314) |
| Contrato | `release-contract-findempro-app-{backend,frontend}.json` (artifacts del run) |

**No hay tag git.** La identidad de esta release es el par (commit, digest), como en
el resto del ecosistema.

### Imágenes — usar el digest, nunca el tag

```
ghcr.io/serius69/findemproai/findempro-app-backend@sha256:d99189d8ee89c77a112acdda5681ce73cc57f0ef95f0ebabf05889b19cfad330
ghcr.io/serius69/findemproai/findempro-app-frontend@sha256:92a71efc86da0a273b948026d41fa7ad31dded75d919b5908cb3b885cb7c65ac
```

> ⚠️ El campo `artifact.image` del contrato dice `ghcr.io/Serius69/FindemproAI/...`
> con mayúsculas, porque `docker/metadata-action` interpola `github.repository` tal cual.
> **Un `docker pull` con esa cadena falla** (`repository name must be lowercase`).
> Las líneas de arriba son la forma correcta. El digest sí es exacto.

El paquete es **privado**: hace falta `docker login ghcr.io` con un token con
`read:packages`. El token de `gh` en este host NO lo tiene, así que desde DEV el
digest está verificado por la salida de `docker/build-push-action` (`digest_source:
registry`), no por un pull.

---

## 2. Qué cambia para el usuario

Esta release arregla que **`/app/` se caía en cada simulación y en cada pronóstico
que terminaban BIEN**. El contrato TypeScript describía una forma que el servidor
nunca emitió, y el render hacía `undefined.map` con cada respuesta 200.

- **Simulación** (`/app/` → Simular): la página ya no se cae. Presenta el beneficio
  **típico (mediana)** además de la media — en una distribución asimétrica no son el
  mismo número, y antes sólo el simulador público veía el p50.
- **Pronóstico** (`/app/` → Pronóstico): la página ya no se cae. Devuelve **RMSE**
  junto a MAPE, de modo que sigue habiendo un indicador de error cuando MAPE no está
  definido (observaciones históricas en cero).
- **Escenarios**: cinco escenarios por percentil de demanda, en vez de tres etiquetas
  Pesimista/Base/Optimista con una "probabilidad" que el servidor nunca publicó.
- **Sharpe ratio / categoría de riesgo**: se muestra «no aplica» y la probabilidad de
  pérdida, en vez de fabricar un valor que el servidor manda como `null`.

Ambos componentes cambian. `frontend_changed: true` **y** `backend_changed: true`.

---

## 3. Evidencia de gates — todos en verde sobre el commit publicado

| Gate | Resultado | Dónde |
|---|---|---|
| Backend pytest (PostgreSQL 16 + Redis 7.2) | **1109 passed / 0 failed / 0 skipped** | run 32806805314, job Gates + `backend-junit.xml` |
| `manage.py check` | sin incidencias | job Gates |
| `makemigrations --check --dry-run` | *No changes detected* | job Gates |
| Frontend typecheck (`tsc -b`) | limpio | job Gates |
| Frontend vitest | 53/53 en 10 archivos | job Gates |
| Frontend contract tests (`node --test`) | 11/11 | job Gates |
| `vite build` | OK | job Gates |
| pip-audit | limpio | run 32805377243 |
| flake8 | limpio | run 32805377243 |
| Docker build smoke | OK | run 32805377243 |

El mismo 1109/0/0 se reprodujo localmente en `tromay-dev` contra
`postgres:16-alpine` + `redis:7.2-alpine`.

---

## 4. Contrato de despliegue

- `schema_change_class: NONE` · `db_changed: false` · `migrations.pending: []`.
  **No hay migración que correr.** `makemigrations --check` confirma que el modelo y
  las migraciones están sincronizados.
- `target_runtime: docker-compose`.
- Backend `stateful: true`, frontend `stateful: false`.
- **Rollback:** volver al digest anterior. Al no haber migración, la imagen previa lee
  el mismo esquema. Los scopes de throttling se declaran por entorno, así que un
  rollback **no** debe combinarse con una reversión parcial de settings.
- `rollback.target_digest` va en `null` en el contrato: PROD debe anotar ahí el digest
  que está corriendo AHORA, antes de cambiarlo. Desde DEV no es observable.

### Variables de entorno obligatorias (backend)

`DJANGO_ENV`, `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DB_ENGINE`, `DB_NAME`,
`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `REDIS_URL`, `CELERY_BROKER_URL`,
`CELERY_RESULT_BACKEND` — y **`DJANGO_ALLOWED_HOSTS`**.

`settings/production.py` es **fail-closed** y sigue siéndolo: sin `SECRET_KEY` o sin
`DJANGO_ALLOWED_HOSTS` el proceso aborta con `ValueError` en el import, no arranca con
un default permisivo. Verificado empíricamente sobre un árbol sin archivos `.env`, que
es lo que hay dentro de la imagen (`.dockerignore` excluye `.env` y `.env.*`).

> ⚠️ **No montar un `.env.production` dentro del contenedor esperando que la garantía
> siga protegiendo.** `settings/__init__.py` despacha por `DJANGO_ENV` y `base.py`
> hace `load_dotenv` de `.env.<entorno>` (o `.env`): cualquier archivo en disco
> satisface el guardia. La garantía protege contra el olvido de la variable, no contra
> un archivo con valores equivocados.

### Healthchecks

`GET /health/live/` → 200 · `GET /health/ready/` → 200 (timeout 10s cada uno).

---

## 5. Verificación post-deploy — flujos primarios

1. Iniciar sesión y llegar al dashboard autenticado.
2. **Crear y correr una simulación** — la página debe RENDERIZAR el resultado
   (es exactamente lo que fallaba). Comprobar que aparece «Beneficio típico (mediana)».
3. **Correr un pronóstico** — debe renderizar y mostrar RMSE junto a MAPE.
4. Leer resultados de flujo de caja y cadena de suministro.
5. Exportar o descargar un resultado.

---

## 6. Lo que queda abierto (decisión de Sergio, no del emisor)

1. **`prod_ready` sigue en `false`** en ambos contratos. Es un campo humano; el emisor
   no lo toca y yo tampoco. Los gates están en verde; la decisión de marcarlo es tuya.
2. **`full-pipeline` no tiene test de regresión.** El arreglo de
   `runFullPipeline(businessId → simulationId)` en `frontend/src/lib/api.ts` es correcto
   —la ruta resuelve por `simulation_id` y sólo podía devolver 404— pero:
   - ningún test cubre el endpoint `FullPipelineAPIView` a nivel HTTP
     (`test_integration.py` prueba el *servicio*, no la vista);
   - **ninguna página de la SPA llama a `runFullPipeline`**: hoy es un export muerto.
   No bloquea la release (no puede romper nada que no esté ya roto), pero el punto 3 de
   tu plan pedía confirmar los tres, y éste es el que no está cubierto.
3. **`ci.yml` sigue fijando Node 20.** Su job de frontend sólo instala y compila, así
   que pasa; si algún día se le añade vitest, fallará igual que falló el gate de release.
4. **El job «Deploy to Production» de `ci.yml` falla** con `missing server host`: no
   tiene configurado el secret del host SSH. Es la ruta vieja de deploy y no participa
   de esta release, pero deja el run de CI en rojo aunque todos los gates pasen.
