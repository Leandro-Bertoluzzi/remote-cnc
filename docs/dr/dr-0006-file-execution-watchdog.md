# DR 0006: Watchdog de stall para la ejecución de archivos G-code

## Status

Accepted

## Date

2026-05-13

## Context and Problem

Durante la ejecución de un archivo G-code, el Gateway envía líneas al buffer de GRBL y espera
un `ok` por cada línea procesada. Si el dispositivo deja de responder (stall) sin que se haya
producido un error explícito (alarm, error:N), el Gateway podría seguir enviando líneas
indefinidamente sin detectar el problema, dejando la tarea en estado `in_progress` para siempre.

Se necesita un mecanismo que detecte este stall y falle la ejecución de forma controlada, sin
cortar la conexión serial (que puede seguir siendo útil para diagnóstico o reconexión).

### Contexto adicional: implementación inicial incorrecta

Una primera versión del watchdog fue implementada dentro de `GrblCommunicator` (capa de I/O
serial). Esa implementación presentaba dos problemas de diseño:

1. **Responsabilidad incorrecta**: `GrblCommunicator` es responsable del I/O serial puro; la
   semántica de "ejecución de archivo" le es ajena. El watchdog sólo tiene sentido mientras un
   archivo está siendo ejecutado.
2. **Efecto colateral incorrecto**: al dispararse, el callback `GrblController._on_stall()` aplicaba
   `set_flag(PAUSED, True)` sobre el estado global del controller. Esto es incorrecto porque GRBL no
   está pausado — simplemente no está respondiendo. Además, el controller debe poder recibir comandos
   en cualquier momento, independientemente de si hubo un stall durante una ejecución previa.

## Options Considered

1. **Watchdog en `GrblCommunicator`** (implementación inicial).
    - Pros: centralizado, siempre activo.
    - Cons: responsabilidad equivocada; aplica efectos globales (pausa) ante un evento que sólo
      es relevante en el contexto de la ejecución de archivos; dispara fuera de ese contexto
      (durante jogging, comandos manuales) donde un timeout de 60 s es irrelevante.

2. **Eliminar el watchdog completamente**.
    - Pros: elimina toda la complejidad.
    - Cons: sin watchdog, un stall durante la ejecución de un archivo dejaría la tarea bloqueada
      indefinidamente. Inaceptable para producción.

3. **Watchdog en `FileExecutor`** ✅ elegida.
    - Pros: el watchdog sólo existe mientras hay un archivo ejecutándose; usa información que
      `FileExecutor` ya posee (`_sent_lines`, `_processed_lines`, `_paused`); sin efectos sobre
      el estado global del controller; permite parametrizar el timeout a nivel de ejecutor;
      simplifica `GrblCommunicator` (sin `_last_ok_time`, sin bloque watchdog, sin parámetro
      `on_stall`).
    - Cons: el watchdog ya no puede detectar stalls fuera del contexto de ejecución de archivos,
      pero ese escenario no requiere manejo automático (jogging y comandos manuales son
      interactivos y el usuario detecta el problema directamente).

## Decision

El watchdog de stall se implementa **exclusivamente en `FileExecutor`**.

**Lógica:** al inicio de cada `tick()`, antes de enviar la siguiente línea, se verifica si hay
comandos enviados pendientes de `ok` (`_sent_lines - _processed_lines > 0`) y si el tiempo
transcurrido desde el último `ok` supera `STALL_TIMEOUT` (60 s). Si la condición se cumple y
la ejecución no está pausada, se llama a `_on_stall()`.

```text
tick()
  ├─ (guard) not _running or _paused → return
  ├─ rate limiter
  ├─ buffer fill check
  ├─ CNC error check
  ├─ stall watchdog:
  │     pending = _sent_lines - _processed_lines
  │     if pending > 0 and (now - _last_ok_time) > STALL_TIMEOUT → _on_stall()
  └─ readline / send
```

`_last_ok_time` se inicializa en `start()` (con `time.time()`) y se actualiza en `_on_ok()`.
Esto garantiza que el timeout empieza a contar desde que se envió el primer comando al que
GRBL no ha respondido, no desde que se abrió el archivo.

**Cambios en capas inferiores:**

- `GrblCommunicator`: se elimina el bloque watchdog, `_last_ok_time`, `STALL_TIMEOUT_SECONDS`
  y el parámetro `on_stall`.
- `GrblController`: se elimina `_on_stall()`, `register_stall_hook()` y `_stall_hook`.

## Consequences

- **[+]** El watchdog sólo actúa en el contexto correcto (ejecución de archivos).
- **[+]** No hay efectos colaterales sobre el estado global del controller.
- **[+]** `GrblCommunicator` se simplifica: responsabilidad única de I/O serial.
- **[+]** El timeout es configurable por módulo (`STALL_TIMEOUT` en `fileExecutor.py`) sin
  afectar otras partes del sistema.
- **[-]** Un stall durante jogging o comandos manuales no se detecta automáticamente. Aceptable
  porque esos flujos son interactivos y el usuario detecta el problema directamente.

## Next Steps

- ✅ Eliminar bloque watchdog, `_last_ok_time`, `STALL_TIMEOUT_SECONDS` y `on_stall` de
  `GrblCommunicator`.
- ✅ Eliminar `_on_stall()`, `register_stall_hook()` y `_stall_hook` de `GrblController`.
- ✅ Implementar `_last_ok_time` y `STALL_TIMEOUT` en `FileExecutor`.
- ✅ Agregar check de stall en `tick()`.
- ✅ Actualizar tests en consecuencia.
