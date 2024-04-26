| **Caso de uso**      | **Aprobar tarea** |
| :---        | :---        |
| **Identificador**      | UC12 |
| **Actores**      | Administrador |
| **Precondición**   | Hay al menos una tarea en estado "pendiente de aprobación". |
| **Resultado**   | El usuario cambia el estado de una tarea a "en espera". |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda aprobar una tarea que está en estado "pendiente de aprobación".

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Tarea", selecciona una tarea en estado "pendiente de aprobación". |  |
| 2      | Cliquea el botón de "Aprobar". |  |
| 4      |  | Pregunta si realmente desea aprobar la tarea. |
| 5      | Selecciona la opción "Sí". |  |
| 3      |  | Actualiza la DB. |
| 8      |  | Actualiza el estado de la tarea en el listado de tareas. |

**Curso alternativo (el usuario se retracta):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 5a      | Cliquea "No". |  |
| 5b      |  | Cierra el mensaje de confirmación. |
