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
| 3      |  | Actualiza la DB. |
| 4      |  | Pregunta si ejecutar la tarea ahora. |
| 5      | Selecciona la opción "Sí". |  |
| 6      |  | Envía la tarea a la cola de ejecución, actualiza estado del worker. |
| 7      |  | Actualiza el estado del worker y la barra de estado. |
| 8      |  | Quita la tarea aprobada del listado de solicitudes. |

**Curso alternativo (decide no ejecutarla):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 5a      | Selecciona la opción "No". |  |
| 5b      |  | Quita la tarea aprobada del listado de solicitudes. |

**Curso alternativo (hay una tarea en ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      |  | Quita la tarea aprobada del listado de solicitudes. |

**Curso alternativo (el equipo está deshabilitado):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      |  | Quita la tarea aprobada del listado de solicitudes. |
