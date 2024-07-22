| **Caso de uso**      | **Restaurar tarea** |
| :---        | :---        |
| **Identificador**      | UC11 |
| **Actores**      | Administrador |
| **Precondición**   | Hay al menos una tarea en estado "cancelada", "rechazada" o "fallida". |
| **Resultado**   | El usuario cambia el estado de una tarea a "en espera". |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda restaurar una tarea cancelada o fallida a su estado inicial.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Tarea", selecciona una tarea en estado "cancelada", "rechazada" o "fallida". |  |
| 2      | Cliquea el botón de "Restaurar". |  |
| 4      |  | Pregunta si realmente desea restaurar la tarea. |
| 5      | Selecciona la opción "Sí". |  |
| 3      |  | Actualiza la DB. |
| 8      |  | Actualiza el estado de la tarea en el listado de tareas. |

**Curso alternativo (el usuario se retracta):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 5a      | Cliquea "No". |  |
| 5b      |  | Cierra el mensaje de confirmación. |
