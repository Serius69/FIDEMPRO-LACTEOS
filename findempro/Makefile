# ══════════════════════════════════════════════════════════
# FINDEMPRO — Makefile de deploy y operaciones
# Uso: make <target>
# ══════════════════════════════════════════════════════════

COMPOSE     = docker compose -f docker-compose.prod.yml
DJANGO_CMD  = $(COMPOSE) exec backend python manage.py
BACKUP_DIR  = ./backups

.DEFAULT_GOAL := help

# ── Ayuda ────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  FINDEMPRO — Comandos disponibles"
	@echo "  ─────────────────────────────────────────────"
	@echo "  make build       Construye las imágenes Docker"
	@echo "  make up          Levanta todos los servicios"
	@echo "  make down        Detiene todos los servicios"
	@echo "  make restart     Reinicia todos los servicios"
	@echo "  make logs        Muestra logs en tiempo real"
	@echo "  make logs-back   Logs solo del backend"
	@echo "  make ps          Estado de los contenedores"
	@echo "  make migrate     Ejecuta migraciones"
	@echo "  make static      Collectstatic"
	@echo "  make shell       Shell Django (dbshell: SQL)"
	@echo "  make createsup   Crea superusuario"
	@echo "  make backup      Backup de la base de datos"
	@echo "  make restore     Restaurar backup (BACKUP=archivo)"
	@echo "  make health      Verifica health check"
	@echo "  make test        Ejecuta tests"
	@echo "  make clean       Elimina contenedores y volúmenes"
	@echo ""

# ── Build ────────────────────────────────────────────────
.PHONY: build
build:
	$(COMPOSE) build --no-cache

.PHONY: build-fast
build-fast:
	$(COMPOSE) build

# ── Ciclo de vida ────────────────────────────────────────
.PHONY: up
up:
	$(COMPOSE) up -d
	@echo "Servicios levantados. Verifica con: make ps"

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: restart
restart:
	$(COMPOSE) restart

.PHONY: restart-back
restart-back:
	$(COMPOSE) restart backend

# ── Logs ────────────────────────────────────────────────
.PHONY: logs
logs:
	$(COMPOSE) logs -f --tail=100

.PHONY: logs-back
logs-back:
	$(COMPOSE) logs -f --tail=100 backend

.PHONY: logs-nginx
logs-nginx:
	$(COMPOSE) logs -f --tail=100 nginx

.PHONY: logs-celery
logs-celery:
	$(COMPOSE) logs -f --tail=100 celery

# ── Estado ──────────────────────────────────────────────
.PHONY: ps
ps:
	$(COMPOSE) ps

# ── Django ──────────────────────────────────────────────
.PHONY: migrate
migrate:
	$(DJANGO_CMD) migrate --noinput

.PHONY: makemigrations
makemigrations:
	$(DJANGO_CMD) makemigrations

.PHONY: static
static:
	$(DJANGO_CMD) collectstatic --noinput

.PHONY: shell
shell:
	$(DJANGO_CMD) shell

.PHONY: dbshell
dbshell:
	$(DJANGO_CMD) dbshell

.PHONY: createsup
createsup:
	$(DJANGO_CMD) createsuperuser

# ── Tests ────────────────────────────────────────────────
.PHONY: test
test:
	$(COMPOSE) exec backend pytest simulate/tests/ -v

.PHONY: test-coverage
test-coverage:
	$(COMPOSE) exec backend pytest simulate/tests/ --cov=simulate --cov-report=html -v

# ── Backup / Restore ─────────────────────────────────────
.PHONY: backup
backup:
	@mkdir -p $(BACKUP_DIR)
	$(COMPOSE) exec db pg_dump -U $${DB_USER:-findempro} $${DB_NAME:-findempro} \
		| gzip > $(BACKUP_DIR)/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup guardado en $(BACKUP_DIR)/"

.PHONY: restore
restore:
	@test -n "$(BACKUP)" || (echo "Uso: make restore BACKUP=backups/archivo.sql.gz" && exit 1)
	zcat $(BACKUP) | $(COMPOSE) exec -T db psql -U $${DB_USER:-findempro} $${DB_NAME:-findempro}
	@echo "Restauracion completada."

# ── Health check ─────────────────────────────────────────
.PHONY: health
health:
	@curl -sf http://localhost/health/ | python3 -m json.tool || echo "UNHEALTHY"

# ── Limpieza ────────────────────────────────────────────
.PHONY: clean
clean:
	@echo "ADVERTENCIA: Esto eliminara contenedores y volumenes."
	@read -p "Continuar? [y/N] " ans && [ "$$ans" = "y" ]
	$(COMPOSE) down -v --remove-orphans
	docker image prune -f

.PHONY: clean-cache
clean-cache:
	$(DJANGO_CMD) shell -c "from django.core.cache import cache; cache.clear(); print('Cache limpiado')"

# ── Deploy completo (primera vez) ────────────────────────
.PHONY: deploy
deploy: build up
	@echo "Esperando que los servicios inicien..."
	@sleep 10
	$(MAKE) migrate
	$(MAKE) static
	@echo ""
	@echo "Deploy completado."
	@$(MAKE) health
