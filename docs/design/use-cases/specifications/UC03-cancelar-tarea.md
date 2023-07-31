| **Caso de uso**      | **Cancelar tarea** |
| :---        | :---        |
| **Identificador**      | UC03 |
| **Actores**      | Usuario |
| **Precondición**   | Hay tareas en espera y/o pendientes de aprobación. |
| **Resultado**   | El usuario quita una tarea de la cola de ejecución. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda cancelar una tarea que no está aun en ejecución.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Administrar tareas". |  |
| 2      |  | Solicita a la DB las tareas en cola y en progreso para el equipo. |
| 3      |  | Muestra al usuario el listado de tareas pendientes de aprobación, en cola de espera y en progreso. |
| 4      | Cliquea el botón "Cancelar" en la tarea correspondiente. |  |
| 5      |  | Muestra el formulario de cancelación de solicitud. |
| 6      | Completa la razón de cancelación y cliquea "Aceptar". |  |
| 7      |  | Actualiza la DB y muestra un mensaje de éxito. |

**Curso alternativo (el usuario se retracta):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 6a      | Cliquea "Cancelar". |  |
| 6b      |  | Cierra el mensaje de confirmación. |
