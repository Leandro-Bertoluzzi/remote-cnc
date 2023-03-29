| **Caso de uso**      | **Ver cola de ejecución** |
| :---        | :---        |
| **Identificador**      | UC05 |
| **Actores**      | Usuario |
| **Precondición**   | El usuario está autenticado y tiene acceso al sistema.<br />Hay una tarea en ejecución. |
| **Resultado**   | El usuario puede ver el estado actual del equipo. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda ver el estado de avance de la tarea actualmente en ejecución y parámetros varios del equipo.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "monitorizar equipo". |  |
| 2      |  | Solicita al servidor una conexión en tiempo real con el equipo. |
| 3      |  | Muestra al usuario el estado de avance de la tarea en progreso y parámetros de interés como temperatura y temperatura de bobinados. |

**Curso alternativo (no hay tareas en ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Recibe del servidor la notificación de que actualmente el equipo está detenido. |
| 3b      |  | Muestra al usuario el mensaje "Actualmente no hay tareas en ejecución en este equipo". |