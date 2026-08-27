# kdp_consumer — copia vendorizada

Origen: `kapitalya-data/kdp_consumer` v2.0.0, copiado el 2026-08-27.

El contrato de migración (`docs/CONTRATO-MIGRACION-CONSUMIDOR.md` §2) obliga a
vendorizar este cliente en vez de reimplementarlo. Un segundo cliente es una
segunda forma de equivocarse con la idempotencia y con el cursor.

**No se edita aquí.** Si hace falta un cambio, se hace en la plataforma y se
vuelve a copiar. Única dependencia: `requests`, que Findempro ya trae.
