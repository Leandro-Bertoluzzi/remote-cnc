| **Caso de uso**      | **Ejecutar tarea** |
| :---        | :---        |
| **Identificador**      | UC23 |
| **Actores**      | Administrador |
| **Precondición**   | Hay al menos una tarea en estado "on hold". |
| **Resultado**   | El usuario puede ordenar la ejecución de una tarea desde el listado de tareas. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda ordenar la ejecución de una tarea en estado "en espera" desde la vista de tareas de los usuarios.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Tareas", selecciona una tarea "en espera". |  |
| 2      | Cliquea el botón de "Ejecutar". |  |
| 3      |  | Envía la tarea a la cola de ejecución. |
| 4      |  | Actualiza el estado del worker y la barra de estado. |
| 5      |  | Actualiza el listado de tareas. |

**Curso alternativo (hay una tarea en ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Muestra una notificación de error. |

**Curso alternativo (el equipo está deshabilitado):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Muestra una notificación de error. |
