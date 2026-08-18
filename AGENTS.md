# AGENTS.md

## Comandos

- Backend Django, desde `findempro/`: `pytest`.
- Frontend React: `cd frontend && npm run dev`, `npm run build`, `npm run lint`, `npm run typecheck`.
- El `npm test` de `findempro/package.json` es un marcador que falla deliberadamente; no usarlo como suite.

## Arquitectura y convenciones

- `findempro/` contiene el proyecto Django y sus dominios (`business`, `finance`, `product`, `questionary`, `report`, `simulate`, `user`, `variable`).
- `frontend/` es React + TypeScript + Vite; `findempro/static/` y `templates/` pertenecen a la interfaz Django heredada.
- `hub_auth/` integra autenticación con el Hub.
- El sistema visual común vive en `platform/design-system/tromay`: usar `TROMAY_DARK`/`TROMAY_LIGHT`, `data-theme` y `localStorage` con clave `kap-theme`. En fondo claro, usar `--kap-green-ink`, nunca `--kap-green`, para texto.

## Pruebas

- Ejecutar `cd findempro && pytest`; la configuración usa ajustes de prueba, marcadores estrictos y marca `slow` para simulaciones grandes.
- Para cambios del frontend ejecutar `cd frontend && npm run lint && npm run typecheck && npm run build`.

## Seguridad

- No leer ni imprimir secretos o `.env`; no exponer información financiera, empresarial o de usuario.
- No ejecutar migraciones ni escribir en bases de datos. No usar los objetivos Make que operan Docker, BD, caché, backups o despliegue.
- Mantener validación y autorización en límites Django/API; no confiar en datos recibidos del cliente.

## Definición de terminado

- Las pruebas y validaciones aplicables pasan sin skips ni reducción de calidad.
- El cambio queda limitado al dominio solicitado y conserva los contratos entre Django, Hub y frontend.
- No se generan migraciones, datos, secretos, builds de imagen ni cambios operativos.

## Rutas autorizadas

- Trabajar únicamente dentro de `apps/public/FindemproAI`.

## Restricciones permanentes

- No tocar `apps/core/forex-erp`, `/mnt/E`, `README.md`, `CLAUDE.md` ni `MEMORY.md`.
- No instalar dependencias, acceder a la red, ejecutar migraciones, escribir en BD, reconstruir imágenes, usar `docker compose up/build`, reiniciar contenedores ni tocar k3s.
- No hacer commit, push, cambiar de rama, ampliar alcance ni realizar refactors oportunistas.
