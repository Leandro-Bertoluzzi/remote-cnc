# DR 0002: Implementar sistema de sesiones con lock distribuido para acceso al CNC

## Status

Accepted

## Date

2026-03-16

## Context and Problem

El puerto serial USB del dispositivo CNC no puede ser compartido. Sin embargo, el sistema tiene múltiples clientes potenciales: la web app (via API), la desktop app, y las tareas Celery de ejecución de archivos. Actualmente no hay ningún mecanismo que impida que dos clientes envíen comandos simultáneamente.

La verificación actual (`is_worker_running()` via Celery inspect, y `are_there_tasks_in_progress()` via SQL) es insuficiente:

- No cubre el caso de dos clientes web enviando comandos por `cnc_server`.
- No cubre Desktop + API operando simultáneamente.
- Las verificaciones son consultas separadas sin atomicidad — vulnerables a race conditions.

El key `worker_enabled` en Redis actúa como un "switch" global que habilita o deshabilita el dispositivo, pero no identifica quién lo está usando ni expira automáticamente.

Se necesita un mecanismo de exclusión mutua que funcione entre todos los clientes, con capacidad de expiración automática por inactividad.

## Options Considered

1. **Lock distribuido con Redis (`SET NX EX`)**: Un key Redis `cnc:session` que actúa como mutex con TTL. El cliente adquiere la sesión, renueva periódicamente (heartbeat), y libera al terminar. Si no renueva, el TTL expira y la sesión se libera sola.
    - Pros: Simple, atómico, con expiración automática. Redis ya está en la infra. Funciona cross-proceso y cross-máquina.
    - Cons: No soporta colas de espera (waiting queue) nativas — si la sesión está ocupada, el cliente recibe rechazo y debe reintentar. Requiere heartbeat del cliente.

2. **Lock con Redlock (multi-instancia Redis)**: Algoritmo de lock distribuido robusto para múltiples instancias Redis.
    - Pros: Más resistente a fallos de Redis.
    - Cons: Overkill — el sistema usa una sola instancia Redis. Complejidad innecesaria.

3. **Lock en base de datos (PostgreSQL advisory locks)**: Usar `pg_advisory_lock()`.
    - Pros: Transaccional, robusto.
    - Cons: No todos los clientes tienen conexión directa a PostgreSQL (la web app usa la API). Mayor latencia. No tiene TTL nativo.

4. **Semáforo interno del Gateway**: El Gateway mantiene un flag interno de sesión activa, sin Redis.
    - Pros: Muy simple.
    - Cons: No visible para otros procesos que quieran consultar si el CNC está ocupado antes de intentar enviar. Pierde estado si el Gateway se reinicia.

## Decision

Se adopta la **opción 1**: lock distribuido con Redis `SET NX EX`.

La sesión se almacena en `cnc:session` como JSON:

```json
{
  "session_id": "uuid-v4",
  "user_id": 1,
  "client_type": "web" | "desktop" | "worker",
  "created_at": "2026-03-16T12:00:00Z"
}
```

El TTL por defecto es 300 segundos (5 minutos), renovable por heartbeat del cliente.

El Gateway valida el `session_id` en cada comando recibido de las colas. Los comandos con `session_id` inválido o ausente se descartan (excepto consultas read-only de estado).

La API expone endpoints de gestión de sesión:

| Método   | Ruta                 | Descripción             |
| -------- | -------------------- | ----------------------- |
| `POST`   | `/cnc/session`       | Adquirir sesión (lock)  |
| `DELETE` | `/cnc/session`       | Liberar sesión          |
| `GET`    | `/cnc/session`       | Consultar sesión activa |
| `PUT`    | `/cnc/session/renew` | Heartbeat (renovar TTL) |

## Consequences

- **[+]** Exclusión mutua atómica cross-proceso — imposible que dos clientes controlen el CNC simultáneamente.
- **[+]** Expiración automática por inactividad — no se queda bloqueado indefinidamente si un cliente se desconecta sin liberar.
- **[+]** Visible para toda la aplicación — cualquier componente puede consultar `cnc:session` para saber si el CNC está en uso y por quién.
- **[+]** Reemplaza las keys `worker_enabled` y `worker_paused` con un mecanismo más robusto y expresivo.
- **[-]** Requiere heartbeat periódico desde el cliente para mantener la sesión viva.
- **[-]** Sin cola de espera nativa — si la sesión está ocupada, el segundo cliente debe reintentar o esperar (puede implementarse como mejora futura con Redis PubSub para notificar liberación).

## Next Steps

- Implementar `sessionManager.py` en el paquete Gateway.
- Agregar endpoints de sesión en la API.
- Integrar validación de sesión en el `commandProcessor` del Gateway.
- Implementar heartbeat en los clientes web y desktop.
- Migrar/eliminar los mecanismos actuales: `worker_enabled`, `worker_paused`, `worker_request` en `WorkerStoreAdapter`.
