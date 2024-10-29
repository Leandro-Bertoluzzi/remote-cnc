| **Caso de uso**      | **Crear tarea** |
| :---        | :---        |
| **Identificador**      | UC02 |
| **Actores**      | Usuario |
| **Precondición**   | Hay al menos un archivo, una herramienta y un material en la base de datos. |
| **Resultado**   | El usuario puede crear una tarea para solicitar su ejecución. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda solicitar la ejecución de una tarea.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Tareas". |  |
| 2      |  | Solicita a la DB las tareas en cola y en progreso para el equipo. |
| 3      |  | Muestra al usuario el listado de tareas pendientes de aprobación, en cola de espera y en progreso. |
| 4      | Cliquea "Crear tarea". |  |
| 5      |  | Despliega una ventana de registro de solicitud. |
| 6      | Completa el nombre, selecciona material y herramienta, y (opcional) agrega un comentario. |  |
| 7      | Presiona "Aceptar". |  |
| 8      |  | Actualiza la DB y muestra una notificación de éxito. |
