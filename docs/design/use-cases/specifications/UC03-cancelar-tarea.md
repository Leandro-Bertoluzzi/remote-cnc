| **Caso de uso**      | **Cancelar tarea** |
| :---        | :---        |
| **Identificador**      | UC03 |
| **Actores**      | Usuario |
| **Precondición**   | El usuario está autenticado y tiene acceso al sistema.<br />Hay tareas en espera y/o pendientes de aprobación. |
| **Resultado**   | El usuario quita una tarea de la cola de ejecución. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda cancelar una tarea que no está aun en ejecución.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "ver cola de ejecución". |  |
| 2      |  | Solicita al servidor las tareas en cola y en progreso para el equipo. |
| 3      |  | Muestra al usuario el listado de tareas pendientes de aprobación, en cola de espera y en progreso. |
| 4      | Cliquea el botón "Cancelar" en la tarea correspondiente. |  |
| 5      |  | Muestra al usuario un mensaje solicitando una confirmación de la cancelación. |
| 6      | Cliquea "Aceptar". |  |
| 7      |  | Envía al servidor la solicitud de cancelación. |
| 8      |  | Muestra un mensaje de éxito/error en la cancelación. |

**Curso alternativo (el usuario se retracta):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 6a      | Cliquea "Cancelar". |  |
| 6b      |  | Cierra el mensaje de confirmación. |