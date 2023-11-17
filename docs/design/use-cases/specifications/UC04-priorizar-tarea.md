| **Caso de uso**      | **Priorizar tarea** |
| :---        | :---        |
| **Identificador**      | UC04 |
| **Actores**      | Administrador |
| **Precondición**   | Hay tareas en espera y/o pendientes de aprobación. |
| **Resultado**   | El usuario cambia el orden de ejecución de tareas en espera. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda cambiar el orden de las tareas que no están aun en ejecución.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Tareas". |  |
| 2      |  | Solicita a la DB las tareas en cola y en progreso para el equipo. |
| 3      |  | Muestra al usuario el listado de tareas pendientes de aprobación, en cola de espera y en progreso. |
| 4      | Selecciona con el cursor y arrastra la tarea correspondiente. |  |
| 5      | Suelta la tarea en la nueva ubicación deseada. |  |
| 6      |  | Actualiza en la DB y muestra un mensaje de éxito. |
