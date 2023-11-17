| **Caso de uso**      | **Ver solicitudes de ejecución** |
| :---        | :---        |
| **Identificador**      | UC11 |
| **Actores**      | Administrador |
| **Precondición**   | -- |
| **Resultado**   | El usuario puede ver un listado de las solicitudes. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda ver un listado de las solicitudes de ejecución (tareas en estado "pendiente de aprobación") de los usuarios.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Solicitudes". |  |
| 2      |  | Solicita a la DB el listado de solicitudes de ejecución. |
| 3      |  | Muestra al usuario el listado de solicitudes. |

**Curso alternativo (no hay solicitudes de tareas):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Recibe un listado vacío de la DB. |
| 3b      |  | Muestra al usuario el mensaje "No hay tareas pendientes de aprobación". |
