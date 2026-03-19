# DR 0004: Mantener Celery como motor de tareas

## Status

Accepted

## Date

2026-03-16

## Context and Problem

El sistema usa Celery con Redis como broker y result backend para ejecutar tareas asincrónicas:

| Tarea              | Tipo                                 | Duración        |
| ------------------ | ------------------------------------ | --------------- |
| `execute_task`     | Ejecución de archivo G-code completo | Minutos a horas |
| `cnc_server`       | Servidor de comandos on-demand       | Indefinida      |
| `create_thumbnail` | Renderizado de miniatura de archivo  | Segundos        |
| `generate_report`  | Análisis estático de archivo G-code  | Segundos        |

Se evaluó la posibilidad de migrar a [Temporal.io](https://temporal.io/) como motor de workflows, motivado por las siguientes limitaciones de Celery en el proyecto:

- **Pause/Resume**: Celery no tiene soporte nativo para pausar/retomar tareas. Actualmente se implementa con flags Redis y polling (`WorkerStatusManager`), lo cual es frágil y agrega latencia.
- **Visibilidad de estado**: Depende de `AsyncResult` y Redis result backend, que no persiste historial y es frágil ante reinicios de Redis.
- **Workflows complejos**: Celery tiene `chain`, `group`, `chord`, pero el manejo de errores y compensación es manual y poco expresivo.
- **Tareas de larga duración**: `execute_task` (~minutos/horas) y `cnc_server` (~indefinida) son loops que no encajan bien en el modelo de Celery, diseñado para tareas finitas.

Temporal ofrece workflows durables, signals/queries nativos, replay determinístico, y una UI completa para depuración.

## Options Considered

1. **Migrar a Temporal**: Reescribir tareas como workflows + activities de Temporal. Agregar servidor Temporal (requiere PostgreSQL adicional) a la infraestructura.
    - Pros: Signals nativos para pause/resume (elimina polling). Queries nativos para estado (elimina `AsyncResult`). Durabilidad automática (si el worker muere, el workflow se retoma). Excelente UI de depuración. Ideal para workflows complejos con compensación.
    - Cons: Temporal server requiere ~512MB RAM + PostgreSQL adicional — difícil de justificar en Raspberry Pi. SDK Python menos maduro que Celery. ~15 archivos impactados, complejidad de migración media-alta. Las tareas fire-and-forget (`create_thumbnail`, `generate_report`) no se benefician significativamente. Overhead de latencia por persistencia de eventos.

2. **Mantener Celery + resolver IPC con Gateway dedicado**: Conservar Celery para tareas finitas. Mover la comunicación serial y el IPC de pause/resume al Gateway (ver [DR 0001](dr-0001-cnc-gateway-process.md) y [DR 0003](dr-0003-priority-command-queues.md)).
    - Pros: Sin cambios de infraestructura (Redis ya existe). Las tareas Celery se simplifican enormemente (ya no manejan serial ni IPC). `chain`/`group` cubren workflows simples. Menor footprint en RPi. Menor riesgo de migración.
    - Cons: No tiene la durabilidad ni el replay determinístico de Temporal. Workflows muy complejos (compensación, branching, parallel sub-workflows) requerirían implementación manual.

3. **Evaluar alternativas ligeras (Dramatiq, Huey, ARQ)**: Reemplazar Celery por un task queue más liviano.
    - Pros: API potencialmente más simple que Celery (especialmente Dramatiq).
    - Cons: Mismo modelo fundamental que Celery (cola de tareas), sin las ventajas de Temporal. Menor ecosistema y comunidad. Costo de migración sin ganancia significativa para los problemas planteados.

## Decision

Se adopta la **opción 2**: mantener Celery y delegar la comunicación serial y el IPC al Gateway.

### Justificación

Los problemas que motivaron la evaluación de Temporal se resuelven con el Gateway + colas Redis sin agregar infraestructura:

| Problema       | Solución con Temporal               | Solución con Gateway                                                      |
| -------------- | ----------------------------------- | ------------------------------------------------------------------------- |
| Pause/Resume   | Signals nativos                     | Cola `cnc:queue:critical` ([DR 0003](dr-0003-priority-command-queues.md)) |
| Estado CNC     | Queries nativos                     | Redis PubSub `grbl_status` (ya existente, unificado)                      |
| Locking serial | N/A (requiere implementación igual) | Sesiones Redis ([DR 0002](dr-0002-session-locking.md))                    |
| Tareas largas  | Workflows durables                  | Gateway siempre activo; tarea Celery solo orquesta DB                     |

Las tareas Celery post-refactor son simples y finitas:

- `execute_task`: Orquesta ciclo de vida en DB → solicita ejecución al Gateway → espera resultado via Redis PubSub → actualiza DB. ~40 líneas, sin loop serial.
- `create_thumbnail`, `generate_report`: Fire-and-forget, sin cambios.
- `cnc_server`: **Eliminada** — el Gateway la reemplaza.

Para encadenar tareas se usarán `chain`/`group` de Celery, que son suficientes para los workflows previstos (ej: analizar → ejecutar → reportar).

### Criterios de reevaluación

Se reconsiderará Temporal si:

- Se agregan más de 5 tipos de workflow con lógica de compensación.
- Se necesita replay/debugging determinístico por regulación o auditoría.
- La infraestructura de producción se migra a un servidor con más recursos (no RPi).

## Consequences

- **[+]** Sin cambios de infraestructura — no se agrega PostgreSQL ni Temporal server a la Raspberry Pi.
- **[+]** Celery sigue manejando lo que hace bien: tareas finitas y asincrónicas.
- **[+]** Los problemas de IPC (pause/resume, estado) se resuelven en la capa del Gateway, dejando a Celery fuera de esa responsabilidad.
- **[+]** Menor riesgo de migración — no se reescribe el motor de tareas completo.
- **[+]** Se eliminan las limitaciones que originalmente motivaron la evaluación de Temporal, sin la complejidad de Temporal.
- **[-]** No se obtiene la durabilidad ni el replay determinístico de Temporal.
- **[-]** Workflows complejos futuros requerirán más trabajo manual con Celery chain/group/chord.
- **[-]** La visibilidad sigue dependiendo parcialmente de Flower + AsyncResult para tareas no-CNC (thumbnails, reportes).

## Next Steps

- Refactorizar `execute_task` para que delegue la comunicación serial al Gateway y se limite a orquestación de DB.
- Eliminar la tarea `cnc_server`.
- Implementar workflows simples con `chain` cuando se necesite encadenar tareas.
- Documentar los criterios de reevaluación de Temporal en este DR para referencia futura.
