# Entornos y archivos `.env*` — FindemproAI

Este directorio acumuló varios archivos de entorno a lo largo del tiempo. Esta
tabla dice, para cada uno, si es el que realmente usa el flujo de dev
(`./scripts/dev-up` en la raíz del repo) y para qué sirve el resto.

## Autoritativo para dev local

**`.env.development`** es el único archivo que lee `docker-compose.dev.yml`
(`env_file: .env.development` en los servicios `findempro_backend`,
`findempro_celery` y `findempro_celery_beat`). Es el que `./scripts/dev-up`
crea automáticamente si falta (con `SECRET_KEY` y `DB_PASSWORD` aleatorios vía
`openssl rand`) y el único que hace falta tocar para desarrollo local con
Docker.

No confundir con el archivo `.env` (sin sufijo, en este mismo directorio):
Docker Compose lo carga *implícitamente* como fuente de sustitución de
variables (`${DB_USER}`, `${DB_PASSWORD}`, etc.) para **todos** los servicios
del compose file, incluido `findempro_db` — que no tiene `env_file` propio.
Si ese `.env` existe, sus valores de `DB_USER`/`DB_PASSWORD`/`DB_NAME` ganan
sobre los defaults inline del compose (`${DB_USER:-findempro}`, …); si no
existe, esos defaults ya son suficientes para levantar el stack de dev sin
tocar nada.

## El resto de los `.env.*`

| Archivo | Uso | ¿Lo lee `docker-compose.dev.yml`? |
|---|---|---|
| `.env` | Sustitución de variables de Docker Compose para **producción** (`docker-compose.prod.yml` usa `env_file: .env` en backend/celery/beat) y, de forma implícita, también para el compose de dev (ver nota arriba). Contiene secretos reales — nunca commitear. | Solo para interpolación de `${VAR}`, no vía `env_file`. |
| `.env.development` | **Dev local (autoritativo, ver arriba).** | Sí — `env_file` explícito. |
| `.env.test` | Referencia para corridas de pytest **fuera de Docker** (`DJANGO_ENV=test`, SQLite `db_test.sqlite3`, puerto documentado 8001). `pytest.ini` en realidad fuerza `DJANGO_SETTINGS_MODULE=findempro.settings.testing` sin depender de este archivo (settings.testing usa SQLite en memoria y no requiere ningún `.env`), así que este archivo es documentación/compatibilidad con `test_start.bat`, no algo que el flujo de test en Docker lea. | No. |
| `.env.staging` | Config de referencia para un entorno de staging (puerto 8002, Postgres `findempro_staging`). No hay `docker-compose.staging.yml` en este repo — es plantilla para un despliegue manual/futuro. | No. |
| `.env.production` | Config de referencia/plantilla para producción real (dominio, SSL, etc.). El compose de producción usa `.env` (ver arriba) como `env_file`, no este archivo directamente. | No. |
| `.env.bak-20260820` | Backup manual de un `.env` anterior, fecha en el nombre. Histórico, no lo lee ningún compose. Conservar como referencia de auditoría; no borrar sin necesidad. | No. |
| `.env.vercel.example` | Plantilla de variables para un despliegue serverless en Vercel (`findempro/settings/vercel.py`). No relacionado con Docker/dev local. | No. |
| `.env.example` | Plantilla general documentada (comentarios en español) usada como base cuando `./scripts/dev-up` necesita generar `.env.development` desde cero. | Solo como template de fallback. |

## Reglas

- No se borra ningún archivo `.env.*` existente como parte de este trabajo de
  estandarización de dev (política explícita: preservar todos).
- Ninguna clave de terceros (Google OAuth, OpenAI, Anthropic, Sentry, Hub SSO,
  SMTP) se inventa nunca al generar `.env.development` — `./scripts/dev-up`
  las deja vacías e imprime un aviso con sus nombres.
- Todos los `.env.*` (salvo `.env.example` y `.env.vercel.example`) están en
  `.gitignore` — no deberían aparecer en `git status` como para commitear.
