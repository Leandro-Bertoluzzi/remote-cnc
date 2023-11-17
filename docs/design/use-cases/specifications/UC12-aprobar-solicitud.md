| **Caso de uso**      | **Aprobar solicitud de ejecución** |
| :---        | :---        |
| **Identificador**      | UC12 |
| **Actores**      | Administrador |
| **Precondición**   | Hay al menos una solicitud de ejecución de un usuario. |
| **Resultado**   | El usuario puede ver un listado de las solicitudes y aprobarlas. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda ver un listado de las solicitudes de ejecución (tareas en estado "pendiente de aprobación") de los usuarios y aprobarlas.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Solicitudes", selecciona una de ellas. |  |
| 2      | Cliquea el botón de "Aprobar". |  |
| 3      |  | Actualiza la DB y muestra una notificación de éxito. |
| 4      |  | Si no hay tareas en progreso, notifica al CNC worker para su ejecución. |
| 5      |  | Bloquea la conexión al equipo desde la vista de "Control manual y calibración". |
| 6      |  | Quita la tarea aprobada del listado de solicitudes. |
