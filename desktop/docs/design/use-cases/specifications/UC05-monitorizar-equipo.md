| **Caso de uso**      | **Monitorizar equipo** |
| :---        | :---        |
| **Identificador**      | UC05 |
| **Actores**      | Usuario |
| **Precondición**   | Hay una tarea en ejecución. |
| **Resultado**   | El usuario puede ver el estado actual del equipo. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda ver el estado de avance de la tarea actualmente en ejecución y parámetros varios del equipo.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Monitoreo". |  |
| 2      |  | Consulta por la información general y configuración del equipo. |
| 3      |  | Consulta regularmente al CNC worker el estado de la ejecución de la tarea actual. |
| 4      |  | Muestra al usuario el estado de avance de la tarea en progreso y parámetros de interés como temperatura y temperatura de bobinados. |

**Curso alternativo (no hay tareas en ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      |  | Recibe del CNC worker la notificación de que actualmente el equipo está detenido. |
| 4b      |  | Muestra al usuario el mensaje "Actualmente no hay tareas en ejecución en este equipo", junto a parámetros de interés como temperatura y temperatura de bobinados. |
