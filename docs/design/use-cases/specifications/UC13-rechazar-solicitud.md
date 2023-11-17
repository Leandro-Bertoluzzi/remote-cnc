| **Caso de uso**      | **Cancelar solicitud de ejecución** |
| :---        | :---        |
| **Identificador**      | UC13 |
| **Actores**      | Administrador |
| **Precondición**   | Hay al menos una solicitud de ejecución de un usuario. |
| **Resultado**   | El usuario puede ver un listado de las solicitudes y rechazarlas. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda ver un listado de las solicitudes de ejecución (tareas en estado "pendiente de aprobación") de los usuarios y rechazarlas.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Solicitudes", selecciona una de ellas. |  |
| 2      | Cliquea el botón de "Rechazar". |  |
| 3      |  | Muestra el formulario de cancelación de solicitud. |
| 4      | Completa la razón de cancelación y presiona el botón de "Aceptar". |  |
| 5      |  | Actualiza la DB y muestra una notificación de éxito. |
| 6      |  | Quita la tarea rechazada del listado de solicitudes. |

**Curso alternativo (el usuario se retracta):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      | Cliquea "Cancelar". |  |
| 4b      |  | Cierra el mensaje de confirmación. |
