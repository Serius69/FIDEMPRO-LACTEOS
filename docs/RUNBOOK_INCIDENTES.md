# Runbook de Incidentes — FindemproAI

**URL:** https://app.kapitalya.com.bo
**Namespace K8s:** `kapitalya`
**Pods normales:** 2 (findemproai-backend, postgres-findemproai)

---

## Diagnóstico rápido

```bash
kubectl get pods -n kapitalya | grep findemproai
kubectl logs -n kapitalya deployment/findemproai --tail=30
kubectl top pod -n kapitalya | grep findemproai
```

---

## Incidente 1 — El sistema no responde (CrashLoopBackOff)

```bash
# Ver estado
kubectl get pods -n kapitalya | grep findemproai

# Logs del crash
kubectl logs -n kapitalya deployment/findemproai --previous | tail -30
# Causas: SECRET_KEY no definida, PostgreSQL caído, migraciones pendientes, allauth mal configurado

# Reiniciar
kubectl rollout restart deployment/findemproai -n kapitalya
kubectl rollout status deployment/findemproai -n kapitalya --timeout=120s

# Verificar que está vivo
curl -s http://findemproai-service.kapitalya.svc.cluster.local/health/live/ | jq .

# Rollback
kubectl rollout undo deployment/findemproai -n kapitalya
```

---

## Incidente 2 — Login no funciona / SSO Hub roto

El SSO **falla cerrado**: ante cualquier duda no emite sesión. Antes de tocar nada, ubicar
en cuál de los tres puntos se corta.

- El flujo lo **inicia FindemproAI** en `/hub/login/`, que fija la cookie `findempro_sso_state`;
  el Hub vuelve solo a `/hub/callback/`. Un enlace que mande `?hub_token=` a otra ruta rebota
  a `/hub/login/` **por diseño** — eso no es una falla, es el canje legado retirado.
- **503 en `/hub/login/` o `/hub/callback/`**: falta `HUB_JWT_SECRET`, o Redis (DB 2, la de
  redención de `state`/`jti`) no responde. Sin poder verificar que un `state`/`jti` no se usó,
  se deniega.
- **Rebote en bucle a `/hub/login/`**: el `state` no coincide, venció (TTL 10 min) o ya se
  consumió. Un reintento limpio del usuario debe funcionar; si no, revisar que la cookie
  llegue (`Secure` requiere HTTPS — ver `DJANGO_DEBUG`).

> Los access logs **redactan a propósito** `hub_token` y `state` (nginx y gunicorn): se ve la
> ruta y el status, nunca el JWT. Es correcto — el project_token es canjeable hasta que expira
> y no puede quedar en un log. No "arreglar" el formato para volver a verlo.

```bash
# Verificar que el Hub esté disponible
curl -s https://kapitalya.com.bo/api/auth/health/ || echo "HUB DOWN"

# Redis de redención del SSO (DB 2): sin él NO se emite sesión
kubectl exec -n kapitalya deployment/findemproai -- \
  python -c "import os,redis; u=os.environ['REDIS_URL'].rsplit('/',1)[0]+'/2'; print(redis.from_url(u, socket_timeout=2).ping())"

# Si el Hub está caído, los usuarios no pueden iniciar sesión.
# El modo offline de allauth (usuario local) sí funciona.

# Ver logs de autenticación
kubectl logs -n kapitalya deployment/findemproai --tail=50 | grep -i "auth\|login\|allauth\|hub\|token"

# Verificar secreto JWT del Hub
kubectl get secret findemproai-secrets -n kapitalya -o jsonpath='{.data.HUB_JWT_SECRET}' | base64 -d | wc -c
# Debe tener > 32 caracteres. Si es 0, el secreto no está configurado.

# Forzar logout de sesiones corruptas
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py shell -c "
from django.contrib.sessions.models import Session
from django.utils import timezone
expired = Session.objects.filter(expire_date__lt=timezone.now())
count = expired.count()
expired.delete()
print(f'Sesiones expiradas eliminadas: {count}')
"
```

---

## Incidente 3 — Simulaciones no completan (timeout / error 500)

```bash
# Ver errores 500 recientes
kubectl logs -n kapitalya deployment/findemproai --tail=100 | grep -i "error\|500\|exception\|traceback" | tail -20

# Verificar que Redis está disponible (usado para cache)
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py shell -c "
from django.core.cache import cache
cache.set('test', 'ok', 10)
print('Redis OK:', cache.get('test'))
"

# Verificar que la DB tiene los datos necesarios para simular
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py shell -c "
from simulate.models import ProbabilisticDensityFunction
print('PDFs activas:', ProbabilisticDensityFunction.objects.filter(is_active=True).count())
"

# Si hay 0 PDFs, el seed es necesario:
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py loaddata --verbosity 2 findempro/fixtures/demo_data.json
```

---

## Incidente 4 — Migraciones rotas (startup falla por schema conflict)

```bash
# Ver estado de migraciones
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py showmigrations 2>&1 | grep "\[ \]"

# Aplicar migraciones pendientes
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py migrate --no-input

# Si una migración está atascada (tabla ya existe):
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py migrate <app_name> <migration_number> --fake
# Por ejemplo: python manage.py migrate simulate 0003 --fake

# Ver el error exacto
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py migrate --no-input 2>&1 | tail -20
```

---

## Incidente 5 — Disco lleno (volúmenes K8s)

```bash
# Ver uso de disco en el pod
kubectl exec -n kapitalya deployment/findemproai -- df -h /

# Limpiar archivos de sesión viejos y archivos media huérfanos
kubectl exec -n kapitalya deployment/findemproai -- \
  python manage.py clearsessions

# Ver el PVC de media
kubectl get pvc -n kapitalya | grep findemproai
# Si el PVC está lleno, aumentar capacidad o limpiar archivos viejos
```

---

## Escalación

**WhatsApp Sergio:** +591-XXXXXXXX
**Email:** sergio.denis.troche.mayta@gmail.com
**SLA recovery:** < 15 minutos (uptime objetivo 99%)
**Incluir:** estado de pods, últimas 20 líneas de logs, URL que falla, cuándo empezó.
