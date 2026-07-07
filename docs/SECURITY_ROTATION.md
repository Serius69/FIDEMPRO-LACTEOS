# Rotación de secretos — FindemproAI

> **Contexto (2026-07-07):** una auditoría detectó secretos reales en texto plano dentro
> de `findempro/.env`, `.env.development` y `.env.production`. Estos archivos están
> excluidos de git (`.gitignore`) y de la imagen Docker (`.dockerignore`), por lo que **no
> se filtran a repositorio ni a la imagen**. Aun así, los secretos que estuvieron en el
> árbol deben considerarse **comprometidos** y rotarse.
>
> `.env.production` ya fue **saneado** (valores reales → placeholders `CAMBIA-ESTO-…`),
> porque en producción los secretos se inyectan vía **K8s Secret**, no desde ese archivo.

## Secretos a rotar (acción manual del usuario)

| Secreto | Dónde estaba | Cómo rotar |
|---------|--------------|-----------|
| **Google OAuth2 Client Secret** (`SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET`, `GOCSPX-…`) | `.env`, `.env.development`, `.env.production` | Google Cloud Console → APIs & Services → Credentials → regenerar secret del OAuth client. Actualizar el K8s Secret. |
| **Gmail App Password** (`EMAIL_HOST_PASSWORD`) | `.env.development`, `.env.production` | Cuenta Google → Seguridad → Contraseñas de aplicación → revocar la actual y crear una nueva. Actualizar K8s Secret. |
| **Django `SECRET_KEY`** | `.env` (valor real) | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` → nuevo valor en K8s Secret. Rotarla invalida sesiones activas. |
| **`DB_PASSWORD`** (`postgres123`, débil) | `.env`, `.env.production` | `ALTER USER findempro WITH PASSWORD '…';` + actualizar K8s Secret. |
| **`REDIS_PASSWORD`** | `.env` | Rotar en el deployment de Redis + K8s Secret. |
| **`HUB_JWT_SECRET`** | compartido entre proyectos | Rotar coordinadamente en TODO el ecosistema Kapitalya (si se rota aquí, romper el resto). |

## Reglas para no reincidir

- **Producción:** todos los secretos van en **K8s `Secret`**, nunca en `ConfigMap` ni en
  archivos `.env` versionados (ver CLAUDE.md del ecosistema).
- **Local:** `findempro/.env` y `.env.development` son solo para desarrollo; ya están en
  `.gitignore` y `.dockerignore`. No poner secretos de producción ahí.
- Plantilla de variables: `findempro/.env.example` (sin valores reales).
- Verificar antes de commitear: `git status` no debe listar ningún `.env` salvo los `*.example`.
