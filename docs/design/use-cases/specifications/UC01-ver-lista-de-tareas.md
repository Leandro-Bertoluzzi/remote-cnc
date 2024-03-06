| **Caso de uso**      | **Ver cola de ejecución** |
| :---        | :---        |
| **Identificador**      | UC02 |
| **Actores**      | Usuario |
| **Precondición**   | -- |
| **Resultado**   | El usuario puede ver un listado de las tareas en ejecución y en espera. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda ver un listado de las tareas en ejecución y en espera.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Tareas". |  |
| 2      |  | Solicita a la DB las tareas pendientes de aprobación, en cola y en progreso para el equipo. |
| 3      |  | Muestra al usuario el listado de tareas pendientes de aprobación y en cola de espera. |

**Curso alternativo (no hay tareas programadas):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Recibe un listado vacío de la DB. |
| 3b      |  | Muestra al usuario el mensaje "La cola de tareas está vacía". |

**Curso alternativo (hay una tarea en ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Consulta al CNC worker el estado de la ejecución de la tarea actual. |
| 3b      |  | Muestra al usuario el listado de tareas pendientes de aprobación, en cola de espera y en ejecución, junto al estado de avance de la tarea en progreso. |
