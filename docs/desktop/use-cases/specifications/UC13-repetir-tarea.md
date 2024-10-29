| **Caso de uso**      | **Repetir tarea** |
| :---        | :---        |
| **Identificador**      | UC13 |
| **Actores**      | Administrador |
| **Precondición**   | Hay al menos una tarea en estado "finalizado". |
| **Resultado**   | El usuario crea una nueva tarea a partir de una finalizada. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda crear una copia de una tarea que está en estado "finalizado".

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Tarea", selecciona una tarea en estado "finalizada". |  |
| 2      | Cliquea el botón de "Repetir". |  |
| 4      |  | Pregunta si realmente desea repetir la tarea. |
| 5      | Selecciona la opción "Sí". |  |
| 3      |  | Actualiza la DB. |
| 8      |  | Actualiza el listado de tareas. |

**Curso alternativo (el usuario se retracta):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 5a      | Cliquea "No". |  |
| 5b      |  | Cierra el mensaje de confirmación. |
