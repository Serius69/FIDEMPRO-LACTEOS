#!/usr/bin/env bash
# scripts/_common.sh — shared helpers for the dev-* scripts.
# Not one of the four entry points; sourced by dev-doctor/dev-up/dev-test/dev-down.
# Intentionally has no `set -euo pipefail` of its own — the sourcing script
# owns that; this file only defines functions/vars.

# Resolve paths relative to THIS file, not the caller's cwd, so every dev-*
# script works no matter where it is invoked from.
_COMMON_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${_COMMON_DIR}/.." &>/dev/null && pwd)"
FINDEMPRO_DIR="${REPO_ROOT}/findempro"
COMPOSE_FILE="${FINDEMPRO_DIR}/docker-compose.dev.yml"
ENV_FILE="${FINDEMPRO_DIR}/.env.development"
ENV_EXAMPLE="${FINDEMPRO_DIR}/.env.example"

# --env-file is pinned to .env.development on purpose: Docker Compose ALSO
# auto-loads a literal `./.env` (if present) for ${VAR} substitution in the
# YAML, independently of any service's `env_file:` list. This repo keeps a
# real `findempro/.env` for docker-compose.prod.yml with production DB
# credentials; without --env-file here, `findempro_db`'s POSTGRES_USER/
# POSTGRES_PASSWORD (substituted from that ambient .env) would silently
# diverge from the postgres/postgres123 that .env.development's env_file
# injects into findempro_backend, and Django's migrate step fails auth. See
# findempro/ENVIRONMENTS.md.
DEV_COMPOSE=(docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}")

# Host ports this product owns in dev (see ENVIRONMENTS.md).
DEV_PORT_DB=55436
DEV_PORT_REDIS=56383
DEV_PORT_BACKEND=58003

log()  { printf '%s\n' "$*" >&2; }
die()  { log "ERROR: $*"; exit 1; }

# port_in_use <port> -> 0 if something is LISTENing on 127.0.0.1:<port>
port_in_use() {
    local port="$1"
    (exec 3<>"/dev/tcp/127.0.0.1/${port}") 2>/dev/null
    local rc=$?
    exec 3>&- 2>/dev/null || true
    exec 3<&- 2>/dev/null || true
    return $rc
}

container_state() {
    # container_state <name> -> prints "missing" | "running" | "stopped"
    local name="$1"
    if ! docker inspect "$name" >/dev/null 2>&1; then
        echo "missing"
        return
    fi
    if [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null)" = "true" ]; then
        echo "running"
    else
        echo "stopped"
    fi
}

container_health() {
    # container_health <name> -> "healthy" | "unhealthy" | "starting" | "none"
    local name="$1"
    docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name" 2>/dev/null || echo "none"
}
