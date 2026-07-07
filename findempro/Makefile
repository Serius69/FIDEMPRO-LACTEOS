# ══════════════════════════════════════════════════════════
# FINDEMPRO — Makefile de deploy y operaciones
# Uso: make <target>
# ══════════════════════════════════════════════════════════

COMPOSE     = docker compose -f docker-compose.prod.yml
DJANGO_CMD  = $(COMPOSE) exec findempro_backend python manage.py
BACKUP_DIR  = ./backups

.DEFAULT_GOAL := help

# ── Ayuda ────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  FINDEMPRO — Comandos disponibles"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make deploy          Build + up + migrate + static + health"
	@echo "  make build           Construye imagenes sin cache"
	@echo "  make build-fast      Construye imagenes con cache"
	@echo "  make up              Levanta todos los servicios"
	@echo "  make down            Detiene todos los servicios"
	@echo "  make restart         Reinicia todos los servicios"
	@echo "  make logs            Muestra todos los logs en tiempo real"
	@echo "  make logs-back       Logs del backend"
	@echo "  make logs-nginx      Logs de nginx"
	@echo "  make logs-celery     Logs del worker Celery"
	@echo "  make ps              Estado de los contenedores"
	@echo "  make migrate         Ejecuta migraciones Django"
	@echo "  make makemigrations  Genera nuevas migraciones"
	@echo "  make static          Collectstatic"
	@echo "  make shell           Shell Django"
	@echo "  make dbshell         Shell PostgreSQL"
	@echo "  make createsup       Crea superusuario"
	@echo "  make test            Ejecuta tests unitarios"
	@echo "  make test-coverage   Tests con reporte de cobertura"
	@echo "  make backup          Backup de la base de datos"
	@echo "  make restore         Restaurar backup (BACKUP=archivo)"
	@echo "  make health          Verifica health check"
	@echo "  make clean           Elimina contenedores y volumenes"
	@echo "  make clean-cache     Limpia cache Redis"
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
	$(COMPOSE) restart findempro_backend

# ── Logs ────────────────────────────────────────────────
.PHONY: logs
logs:
	$(COMPOSE) logs -f --tail=100

.PHONY: logs-back
logs-back:
	$(COMPOSE) logs -f --tail=100 findempro_backend

.PHONY: logs-nginx
logs-nginx:
	$(COMPOSE) logs -f --tail=100 findempro_nginx

.PHONY: logs-celery
logs-celery:
	$(COMPOSE) logs -f --tail=100 findempro_celery

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
	$(COMPOSE) exec findempro_db psql -U $${DB_USER:-findempro} $${DB_NAME:-findempro}

.PHONY: createsup
createsup:
	$(DJANGO_CMD) createsuperuser

# ── Tests ────────────────────────────────────────────────
.PHONY: test
test:
	$(COMPOSE) exec findempro_backend python -m pytest simulate/tests/ -v

.PHONY: test-coverage
test-coverage:
	$(COMPOSE) exec findempro_backend python -m pytest simulate/tests/ --cov=simulate --cov-report=html -v

# ── Backup / Restore ─────────────────────────────────────
.PHONY: backup
backup:
	@mkdir -p $(BACKUP_DIR)
	$(COMPOSE) exec findempro_db pg_dump -U $${DB_USER:-findempro} $${DB_NAME:-findempro} \
		| gzip > $(BACKUP_DIR)/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup guardado en $(BACKUP_DIR)/"

.PHONY: restore
restore:
	@test -n "$(BACKUP)" || (echo "Uso: make restore BACKUP=backups/archivo.sql.gz" && exit 1)
	zcat $(BACKUP) | $(COMPOSE) exec -T findempro_db psql -U $${DB_USER:-findempro} $${DB_NAME:-findempro}
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
	$(COMPOSE) exec findempro_redis redis-cli FLUSHALL

# ── Deploy completo ──────────────────────────────────────
.PHONY: deploy
deploy: build up
	@echo "Esperando que los servicios esten saludables..."
	@$(COMPOSE) exec findempro_backend sh -c \
		'until curl -sf http://localhost:8000/health/live/ > /dev/null 2>&1; do sleep 3; done'
	$(MAKE) migrate
	$(MAKE) static
	@echo ""
	@echo "Deploy completado."
	@$(MAKE) health
