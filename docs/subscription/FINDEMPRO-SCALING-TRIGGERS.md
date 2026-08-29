# Triggers de escalado de Findempro

No se recomienda hardware concreto. Estos triggers obligan a volver a medir o cambiar la
topología antes de aumentar capacidad comercial.

`CURRENT_HARDWARE_SUFFICIENT_TO=100_PAID_PLUS_300_FREE_AT_CONCURRENCY_15_IN_DECLARED_DEV_RUNTIME`

| Señal | Trigger medible | Acción técnica |
|---|---|---|
| CPU_HEADROOM | mean >70% o peak >85% durante 15 min | Perfilar simulaciones por tamaño y separar/scheduler workers |
| RAM_HEADROOM | MemAvailable <2 GB o proceso >85% RAM | Detener escalado; perfilar allocations/result sets |
| DB_LATENCY | submit p95 >=400 ms, interactive p95 >=400 ms o cualquier lock sostenido | Perfil de hot queries/indexes/transacciones; repetir before/after |
| QUEUE_DEPTH | depth >40 sostenida 5 min o drain >60 s | Reducir admisión/concurrencia; medir workers sin perjudicar HTTP |
| SIMULATION_WAIT_TIME | p95 wait >=30 s | Aplicar backpressure/prioridad y separar compute |
| STORAGE_GROWTH | disco libre <20% o forecast <90 días | Revisar retención/result storage y medir delta real |
| ERROR_RATE | >=0.5% warning o >=1% fail por clase | Detener escalado y localizar causa |
| TENANT/METERING | cualquier cross-tenant o atribución incorrecta | P0_SECURITY; detener benchmark |

`NEXT_CAPACITY_TRIGGER=CONCURRENCY_ABOVE_15_OR_SIMULATION_SUBMIT_P95_AT_400MS_OR_QUEUE_SUSTAINED_ABOVE_40`

La frontera DEV observada está entre concurrencia 15 y 25 con 100 paid + 300 Free. No se debe
subir el límite a 25 ni presentar S3/S4 como proyección. S3 se bloqueó por swap libre <512 MB;
S4 además superaba 2500 Organizations sintéticas totales. Ambos deben repetirse solo con
preflight seguro y sin degradar `tromay-dev`.

La próxima campaña relevante no es comprar hardware: es ejecutar el mismo harness contra la
topología DEV candidata con PostgreSQL, Redis y servidor WSGI equivalentes, conservando los SLO,
la mezcla y los invariantes de seguridad.
