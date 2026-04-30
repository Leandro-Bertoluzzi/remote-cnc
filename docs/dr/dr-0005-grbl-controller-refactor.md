# DR 0005: Refactor del controlador GRBL

## Status

Accepted

## Date

2026-04-30

## Context and Problem

La clase `GrblController` concentra demasiadas responsabilidades:

- Gestiona el thread de I/O serial (`serial_io`)
- Mantiene la contabilidad del buffer RX de GRBL (`cline`/`sline`/`_sumcline`)
- Parsea respuestas, encola comandos
- Gestiona el proceso de inicialización y conoce la variable de entorno `GRBL_SIMULATION`

Esto dificulta el testing unitario, el mantenimiento y la extensión del código.

El repositorio de referencia _Universal G-Code Sender (UGS)_ resuelve este problema usando composición: `GrblController` delega en:

- `GrblCommunicator` (I/O puro)
- `GrblControllerInitializer` (protocolo de inicialización)
- Clases de comandos (`GetBuildInfoCommand`, `GetStatusCommand`, etc.)

Adicionalmente se identificaron dos brechas funcionales respecto a UGS:

1. **Carry-forward de WCO y overrides**: GRBL no incluye `WCO:` ni `Ov:` en cada respuesta de status.
   Si estos campos no se conservan entre polls, la posición de trabajo calculada es incorrecta y los
   overrides se pierden.
2. **Inicialización incompleta**: la configuración de GRBL (`$$`) no se solicita automáticamente al
   conectar; el consumidor debe invocar `query_grbl_settings()` manualmente.

```
Arquitectura actual
───────────────────
  GrblController
  ├── serial_io (thread I/O)
  ├── _sumcline / cline / sline
  ├── parse_response
  ├── connect / disconnect
  ├── GRBL_SIMULATION (var. entorno)
  ├── GrblStatus  ← ya extraído
  └── GrblMonitor ← ya extraído

Arquitectura propuesta
──────────────────────
  GrblController  (coordinador)
  ├── GrblCommunicator   (thread I/O puro)
  ├── GrblInitializer    (protocolo de inicialización)
  ├── GrblStatus         (estado — sin cambios)
  ├── GrblMonitor        (logging/pubsub — sin cambios)
  └── commands/          (comandos de consulta estructurada)
      ├── GetBuildInfoCommand
      ├── GetSettingsCommand
      ├── GetParserStateCommand
      └── GetStatusCommand
```

## Options Considered

### Separación de I/O (GrblCommunicator)

1. **Extraer `GrblCommunicator`** con el thread `serial_io`, `cline`/`sline` y detección de comandos EEPROM.
    - Pros: alinea con UGS; `GrblController` queda como coordinador puro; facilita testing del I/O en forma
      independiente.
    - Cons: requiere refactorizar todas las referencias internas a las listas `cline`/`sline`.

2. **Mantener todo en `GrblController`**.
    - Pros: sin cambios de superficie.
    - Cons: mantiene el problema de clase monolítica; testing difícil.

### Clases de comandos

1. **Solo comandos de consulta estructurada** (4 clases: `GetBuildInfoCommand`,
   `GetSettingsCommand`, `GetParserStateCommand`, `GetStatusCommand`).
    - Pros: encapsula el parsing cerca de quien produce los datos; facilita edge cases (GRBL 0.9,
      respuesta mínima `ok`); sin sobreingeniería.
    - Cons: inconsistencia con comandos de acción (`$X`, `$C`, `$H`) que permanecen como strings en el
      enum `GrblCommand`.

2. **Clase para cada comando GRBL** (incluyendo acciones).
    - Pros: consistencia total.
    - Cons: sobreingeniería para comandos que no tienen respuesta estructurada.

### GRBL_SIMULATION

1. **Parámetro `skip_startup_validation: bool`** en `GrblInitializer`.
    - Pros: desacopla la lógica de negocio de la variable de entorno; testeable sin parches de entorno.
    - Cons: el consumidor (gateway) debe pasar el parámetro al construir el inicializador.

2. **Subclase `GrblSimulationInitializer`**.
    - Pros: polimorfismo limpio.
    - Cons: complejidad innecesaria para un solo punto de variación.

3. **Mantener `if not GRBL_SIMULATION`** en `GrblController`.
    - Pros: sin cambios.
    - Cons: el acoplamiento a la variable de entorno permanece en la lógica de negocio.

### Carry-forward de WCO/overrides

1. **En `GrblStatus.update_status()`**.
    - Pros: centralizado; único punto de mantenimiento; testeable en forma aislada.
    - Cons: `GrblStatus` necesita conocer la lógica de derivación de posición.

2. **En `GetStatusCommand.parse()`**.
    - Pros: el parsing vive junto al comando que lo produce.
    - Cons: `GetStatusCommand` necesita acceso al status anterior.

## Decision

Se adoptan las opciones 1 de cada sección:

- **`GrblCommunicator`**: extrae el thread `serial_io`, `cline`/`sline`, `_sumcline`, `_empty_queue`,
  `_send_realtime`, y agrega detección de comandos EEPROM con modo single-step temporal.
- **Clases de comandos**: solo las 4 de consulta estructurada, en el subdirectorio `commands/`.
- **`GRBL_SIMULATION`**: se mantiene en `config.py` pero se pasa como parámetro `skip_startup_validation`
  al construir `GrblInitializer`; el `import GRBL_SIMULATION` se elimina de `grblController.py`.
- **`GrblInitializer`**: protocolo de 5 pasos (poll de status × 10, respuesta a HOLD/ALARM, `$I`, `$G`, `$$`).
- **Carry-forward**: implementado en `GrblStatus.update_status()`.

## Consequences

- **[+]** `GrblController` queda como un coordinador delgado; cada clase tiene una única responsabilidad.
- **[+]** El testing del I/O serial, del protocolo de inicialización, y del parsing de status se puede realizar
  de forma totalmente independiente.
- **[+]** La configuración de GRBL (`$$`) y el estado del parser (`$G`) se obtienen automáticamente al conectar.
- **[+]** La posición de trabajo y los overrides se calculan correctamente entre polls que no incluyen `WCO:` ni `Ov:`.
- **[+]** Los comandos que escriben EEPROM no corrompen el buffer RX gracias al modo single-step temporal en `GrblCommunicator`.
- **[-]** La superficie de la API pública aumenta (3 nuevas clases + 4 comandos
    - 5 pasos de inicialización); la curva de aprendizaje para nuevos colaboradores es algo mayor.
- **[-]** Los tests existentes de `serial_io` y `connect` deben migrarse a los nuevos archivos de test.

## Next Steps

1. Crear `GrblCommunicator` en `src/core/core/utilities/grbl/grblCommunicator.py`.
2. Crear clases de comandos en `src/core/core/utilities/grbl/commands/`.
3. Crear `GrblInitializer` en `src/core/core/utilities/grbl/grblInitializer.py`.
4. Actualizar `GrblStatus.update_status()` con carry-forward de WCO/overrides.
5. Simplificar `GrblController` para delegar en las nuevas clases.
6. Migrar y ampliar los tests correspondientes.
