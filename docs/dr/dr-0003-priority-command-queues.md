# DR 0003: Cola de prioridad para comandos CNC

## Status

Proposed

## Date

2026-03-16

## Context and Problem

El refactor introduce un Gateway CNC (ver [DR 0001](dr-0001-cnc-gateway-process.md)) que recibe comandos de múltiples fuentes (API, Desktop, tareas Celery). Es necesario priorizar ciertos tipos de comandos:

- **Críticos** (pause, resume, stop): Deben procesarse inmediatamente, incluso durante la ejecución de un archivo.
- **Interactivos** (comandos de usuario, jog): Mayor prioridad que líneas de archivo.
- **Archivo** (líneas G-code de ejecución secuencial): Prioridad normal.

Actualmente, la tarea `cnc_server` recibe comandos via Redis PubSub (canal `worker_commands`), sin priorización. Los comandos de pause/resume se manejan por un mecanismo separado de flags Redis (`worker_request`) con polling — una solución frágil que:

- Usa `GET` + `DELETE` no-atómicos en `WorkerStatusManager.get_request()`.
- Requiere que el loop de la tarea Celery haga polling periódico de las flags.
- Es unidireccional: el cliente no recibe confirmación de que el comando se procesó.
- No es extensible a nuevos tipos de comandos sin agregar más flags.

Se requiere un mecanismo unificado de recepción de comandos con soporte de prioridad y bloqueo (para no consumir CPU en busy-waiting).

## Options Considered

1. **Múltiples listas Redis con `BLPOP`**: Tres listas (`cnc:queue:critical`, `cnc:queue:high`, `cnc:queue:normal`). El consumidor ejecuta `BLPOP cnc:queue:critical cnc:queue:high cnc:queue:normal 1`. Redis devuelve el primer elemento del primer key no vacío, respetando el orden de los keys.
    - Pros: Simple, nativo de Redis, con bloqueo (no polling). Prioridad implícita por orden de keys. Atómico (un solo consumidor recibe cada mensaje). Sin dependencias adicionales.
    - Cons: Prioridad estricta (starvation teórica si la cola crítica nunca se vacía, pero en la práctica los comandos críticos son infrecuentes). No soporta prioridad numérica flexible.

2. **Redis Sorted Set (`ZADD`/`BZPOPMIN`)**: Un solo sorted set con score como prioridad.
    - Pros: Prioridad numérica flexible.
    - Cons: `BZPOPMIN` requiere Redis 5.0+ (disponible). Más complejo de implementar. Un solo contenedor para todos los tipos de mensaje mezclados. Scores hay que gestionarlos manualmente.

3. **Redis Streams (`XADD`/`XREAD`)**: Streams con consumer groups.
    - Pros: Persistencia, acknowledgement, consumer groups.
    - Cons: Significativamente más complejo. No tiene prioridad nativa — se necesitarían múltiples streams (volviendo al patrón de opción 1 con más overhead). Over-engineering para el caso de uso.

4. **Message broker dedicado (RabbitMQ con priority queues)**: Cola con soporte nativo de campos de prioridad.
    - Pros: Prioridad nativa, robusta, acknowledgement.
    - Cons: Agrega un servicio de infraestructura (inaceptable en Raspberry Pi con recursos limitados). Redis ya está disponible y es suficiente.

5. **PubSub Redis (modelo actual para comandos on-demand)**: Publicar comandos y que el Gateway se suscriba.
    - Pros: Ya implementado en la tarea `cnc_server`.
    - Cons: No tiene prioridad. Los mensajes se pierden si el suscriptor no está conectado (fire-and-forget). No es una cola — no persiste mensajes. No garantiza orden ni entrega.

## Decision

Se adopta la **opción 1**: múltiples listas Redis con `BLPOP`. Se definen tres niveles:

| Lista Redis          | Prioridad | Contenido                                       |
| -------------------- | --------- | ----------------------------------------------- |
| `cnc:queue:critical` | Máxima    | pause, resume, stop, soft_reset, status queries |
| `cnc:queue:high`     | Alta      | Comandos de usuario (terminal, jog)             |
| `cnc:queue:normal`   | Normal    | Líneas de archivo G-code durante ejecución      |

### Protocolo de mensajes

Cada mensaje en la cola es un string JSON con la siguiente estructura:

```json
{
  "type": "command" | "realtime" | "file_start" | "file_stop",
  "payload": {
    "command": "G0 X10 Y20"
  },
  "session_id": "uuid-v4",
  "timestamp": 1710590400
}
```

Los productores (`GatewayClient`) hacen `RPUSH` a la lista correspondiente según el tipo de comando. El consumidor en el Gateway ejecuta:

```
BLPOP cnc:queue:critical cnc:queue:high cnc:queue:normal 1
```

Esto garantiza que el comando de mayor prioridad disponible se procesa primero, con bloqueo de 1 segundo (no busy-waiting).

## Consequences

- **[+]** Mecanismo unificado de recepción de comandos — elimina la dualidad PubSub (para comandos on-demand) + flags Redis (para pause/resume).
- **[+]** Prioridad estricta garantiza que pause/resume se procesan antes que cualquier línea de archivo.
- **[+]** Bloqueo nativo (`BLPOP`) — sin polling ni busy-waiting.
- **[+]** Atomicidad — cada comando es consumido por exactamente un lector (el Gateway).
- **[+]** Extensible — agregar un nuevo nivel de prioridad solo requiere una nueva lista Redis.
- **[-]** Starvation teórica de la cola normal si las colas superiores siempre tienen elementos (improbable en la práctica: los comandos críticos e interactivos son esporádicos).
- **[-]** Los mensajes se pierden si Redis se reinicia (aceptable — el sistema ya depende de Redis en memoria para el broker Celery con la misma limitación).

## Next Steps

- Implementar `commandProcessor.py` en el Gateway con el consumer loop `BLPOP`.
- Crear `GatewayClient` en `core/utilities/` con métodos `send_command()`, `send_realtime()` que hagan `RPUSH` a la lista correspondiente.
- Migrar `cncRoutes.py` para usar `GatewayClient` en lugar de Redis PubSub.
- Eliminar `WorkerStoreAdapter.request_pause/resume` y las keys `worker_request` / `worker_paused`.
