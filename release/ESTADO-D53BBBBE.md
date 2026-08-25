# FindemproAI — estado reconciliado tras `d53bbbbec`

    FECHA=2026-08-25            HOST=tromay-dev (DESARROLLO)
    MAIN=97dfa02dba0ca9fead3b17cd55b0f86cb3fd1646
    RELEASE_CONSTRUIDA=d53bbbbecf6820c7a72528b9c4c62dee2b9c6396
    MUTACIONES_EN_PROD=NINGUNA

`main` va un commit por delante del que se construyó: `97dfa02db` sólo trae los contratos
que emitió el run de release. El sujeto de la release es `d53bbbbec`, que es lo que declaran
`repo.commit` y `org.opencontainers.image.revision` de las dos imágenes. No se re-lanzó el
release para igualar los SHA: eso es una persecución sin final y el contrato ya nombra sin
ambigüedad lo que se construyó.

## Tres cosas separadas que no hay que mezclar

| | Estado | Evidencia |
|---|---|---|
| **QUALITY_GATES** | **PASS** | Los 7 jobs de calidad de `ci.yml` en verde sobre main (run 32850339131) |
| **RELEASE_READY** | **NO** | `prod_ready: false` en los dos contratos. Es un campo humano; el emisor no lo toca y esta sesión tampoco |
| **AUTOMATIC_DEPLOY_CONFIGURED** | **NO** | El job «Deploy to Production» falla con `missing server host`: el secret `DEPLOY_HOST` no está configurado |

El run de CI sobre main figura en **rojo**, y eso **no** significa que un gate de calidad
haya fallado. Falla únicamente el job de deploy, que es la ruta vieja de build-on-server por
SSH. Leer el rojo del run como "la release no pasa" es exactamente el error que esta tabla
existe para evitar.

**No se creó `DEPLOY_HOST` ni se habilitó el auto-deploy.** Configurarlo convierte cada push
a main en un despliegue a producción, y esa es una decisión de operación, no de esta sesión.
La preferencia declarada es release verificable + handoff explícito, con el despliegue
controlado por el workstream de PROD.

## Artefacto publicado

    IMAGE     ghcr.io/Serius69/FindemproAI/findempro-app-backend:main
    DIGEST    sha256:4fe0eb5fefb197fb29580d8a94a43b07a453af4e05ef66f237ac13de5667f5aa

    IMAGE     ghcr.io/Serius69/FindemproAI/findempro-app-frontend:main
    DIGEST    sha256:0b7a5845d38e05af59b08ffafb171bbead9c29d384a585aaa0b77222bfd22f59

    SOURCE_SHA      d53bbbbecf6820c7a72528b9c4c62dee2b9c6396
    OCI_REVISION    d53bbbbecf6820c7a72528b9c4c62dee2b9c6396
    DIGEST_SOURCE   registry (no es un image id local)

Digest real de registry, así que **no hace falta artefacto offline**: hay imagen exacta
publicada para este SHA.

## Estado de producción — observado, no supuesto

    PROD_DEPLOYED   SÍ    https://app.kapitalya.com.bo
    /health/        200   {"status":"healthy","checks":{"database":"ok","cache":"ok","redis":"ok"}}
    /health/ready/  200   {"status":"ready","database":"ok"}

    CURRENT_PROD_SHA  DESCONOCIDO

No hay endpoint de versión y el despliegue vigente se hizo por la ruta SSH build-on-server,
que no deja digest. **No se infiere**: producción está viva y sana, pero *qué* commit corre
no se puede afirmar desde DEV.

Lo que sí se puede afirmar: **producción NO corre esta release.** El job de deploy nunca
llegó a ejecutarse con éxito, así que lo que está servido es anterior a `d53bbbbec`. Por lo
tanto los dos arreglos de esta release **siguen vivos en producción**:

1. `/simulate/` responde 500 a cualquier usuario con sesión. Y no es una URL que haya que
   escribir a mano: anónimo devuelve `302 → /account/login/?next=/simulate/`, o sea que el
   propio flujo de login deposita al usuario justo encima del 500. Comprobado hoy contra
   producción, sin autenticarse.
2. El contexto macro sale del valor curado: dólar oficial 6,96 cuando el observado es 11,50.
   Toda simulación de PyME —costos de importación, márgenes, precios— parte de ahí.

## Lo que hace falta para desplegar

Esta sesión no despliega y no puede: PROD corre en el host `tromay`, fuera del alcance de
tromay-dev. El workstream de PROD tiene todo lo necesario:

1. Imagen exacta con digest de registry (arriba) — `docker pull` por digest, no por tag.
2. `rollback.target_digest` sigue en `null` porque **es la primera release por esta ruta**:
   lo desplegado hoy no vino de un registry y no tiene digest al que volver. Antes de rodar,
   registrar la imagen viva actual como objetivo de rollback.
3. Aceptación pública mínima tras rodar: entrar con sesión y comprobar que `/simulate/`
   **redirige** en vez de dar 500, y que una simulación pinta el resultado.
