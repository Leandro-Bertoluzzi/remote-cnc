# DR 0001: Introducir un proceso CNC Gateway dedicado para la comunicación serial

## Status

Accepted

## Date

2026-03-16

## Context and Problem

Actualmente, la comunicación con el dispositivo CNC (GRBL via USB/serial) se realiza desde dos puntos completamente independientes:

1. **Worker Celery** — Las tareas `execute_task` y `cnc_server` en `src/worker/worker/tasks/cnc.py` instancian `GrblController`, abren el puerto serial, ejecutan un loop de comunicación, y desconectan al terminar.
2. **Desktop app (ControlView)** — `src/desktop/desktop/views/ControlView.py` instancia su propio `GrblController` y se conecta directamente al puerto serial local.

Estos dos modos no tienen coordinación entre sí. No hay ningún mecanismo de locking distribuido que impida que ambos (o dos tareas Celery simultáneas) intenten abrir el mismo puerto serial. La verificación `are_there_tasks_in_progress()` es una consulta SQL sin lock, vulnerable a race conditions.

Además, la tarea `cnc_server` es una tarea Celery de larga duración que ocupa el único slot de concurrency del worker indefinidamente para recibir comandos on-demand por Redis PubSub — un uso inadecuado del modelo de Celery (diseñado para tareas finitas).

Se requiere unificar el acceso al puerto serial en un único punto para garantizar exclusividad, simplificar la arquitectura y habilitar una cola de comandos con prioridad.

### Arquitectura actual

```
┌──────────┐  REST/SSE   ┌──────────┐  Celery task   ┌────────────────┐  Serial
│  Web App │────────────▶│   API    │──────────────▶│    Worker      │────────▶ CNC
└──────────┘             └──────────┘               │  (cnc_server)  │
                                                    │  (execute_task)│
                                                    └────────────────┘  Serial
┌──────────┐  Direct serial                                           ────────▶ CNC
│ Desktop  │──────────────────────────────────────────────────────────┘
└──────────┘
```

Problemas:

- Dos caminos independientes al puerto serial sin coordinación.
- `cnc_server` ocupa un worker Celery indefinidamente.
- Sin locking del puerto serial; race conditions posibles.
- Duplicación de lógica de conexión/desconexión en worker y desktop.
- Pause/Resume implementado con flags Redis + polling (frágil).

## Options Considered

1. **Mantener el modelo actual con locks adicionales**: Agregar un lock distribuido (Redis `SETNX`) antes de abrir el puerto serial en cada tarea Celery y en el Desktop.
    - Pros: Cambio mínimo, no requiere un nuevo proceso.
    - Cons: No resuelve el problema de `cnc_server` como tarea Celery de larga duración. Cada tarea sigue gestionando conexión/desconexión serial. Duplicación de lógica. No habilita colas de prioridad.

2. **Proceso CNC Gateway dedicado (siempre conectado)**: Un proceso independiente que posee la conexión serial exclusiva, recibe comandos por colas Redis, y publica estado por Redis PubSub.
    - Pros: Punto único de acceso al serial — elimina race conditions por diseño. Permite cola de prioridad. Elimina la tarea `cnc_server`. Simplifica las tareas Celery (ya no manejan serial). Habilita agregar sistema de sesiones y locking.
    - Cons: Nuevo servicio para deployar y mantener. Agrega un hop de latencia (cliente → Redis → Gateway → serial). Requiere refactor significativo.

3. **Embeber el "Gateway" dentro del worker Celery como thread de fondo**: Al iniciar el worker, levantar un thread que mantiene la conexión serial y sirve comandos.
    - Pros: No requiere un nuevo servicio Docker. Reutiliza la infra existente.
    - Cons: Acopla dos responsabilidades en un proceso (tareas Celery + serial). Si el worker se reinicia, se pierde la conexión serial. Debugging más complejo. Celery no está diseñado para gestionar threads de larga duración ajenos a tareas.

## Decision

Se adopta la **opción 2**: crear un proceso CNC Gateway dedicado. Se implementa como un nuevo paquete `src/gateway/` con su propio Dockerfile y servicio Docker.

### Arquitectura propuesta

```
┌──────────┐  REST/SSE  ┌──────────┐              ┌────────────────┐
│  Web App │───────────▶│   API    │─── Redis ───▶│   CNC Gateway  │──── Serial ──▶ CNC
└──────────┘            └──────────┘              │  (always-on)   │
                                                  └────────────────┘
┌──────────┐  REST/Redis ┌──────────┐                    ▲
│ Desktop  │────────────▶│   API    │──── Redis ─────────┘
└──────────┘             └──────────┘
                    ┌────────────────┐
                    │  Celery Worker  │─── Redis ──────┘
                    │  (file tasks)   │
                    └────────────────┘
```

El Gateway:

- Se conecta al dispositivo GRBL al iniciar y mantiene la conexión activa.
- Recibe comandos a través de colas Redis con prioridad (`BLPOP` sobre múltiples listas).
- Publica estado del CNC periódicamente en el canal Redis PubSub `grbl_status`.
- Publica eventos de ciclo de vida (`file_finished`, `file_failed`) en canal `cnc:events`.

## Consequences

- **[+]** Punto único de acceso al serial — elimina la posibilidad de conexiones simultáneas por diseño.
- **[+]** La tarea Celery `cnc_server` se elimina; los comandos on-demand van directo al Gateway sin necesidad de una tarea Celery intermediaria.
- **[+]** La tarea `execute_task` se simplifica a orquestación de DB; ya no maneja serial.
- **[+]** Habilita cola de prioridad para comandos (pause/resume > jog > líneas de archivo).
- **[-]** Nuevo servicio que requiere deployment, monitoreo y documentación.
- **[-]** Un hop adicional de latencia (~1-5ms por el paso por Redis), aceptable para las frecuencias de comunicación actuales (~10 comandos/s).
- **[-]** Refactor significativo en worker, API, y Desktop.

## Next Steps

- Implementar paquete `src/gateway/`.
- Agregar servicio `gateway` en `docker-compose.yaml`.
- Migrar `cncRoutes` y `workerRoutes` para comunicarse con el Gateway.
- Migrar Desktop `ControlView` para usar el Gateway en lugar de `GrblController` directo.
