| **Caso de uso**      | **Aprobar solicitud de ejecución** |
| :---        | :---        |
| **Identificador**      | UC12 |
| **Actores**      | Administrador |
| **Precondición**   | El equipo se encuentra deshabilitado. |
| **Resultado**   | El usuario puede habilitar manualmente el equipo. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda habilitar el equipo para procesar una nueva tarea. El equipo es deshabilitado automáticamente cuando se completa una tarea, para permitir al operario preparar el equipo (cambiar material y/o herramienta, realizar algún ajuste o prueba manual) para la ejecución de la siguiente tarea.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la barra de estado de la aplicación, cliquea el botón de "habilitar". |  |
| 2      |  | Actualiza el estado del dispositivo y habilita la ejecución de tareas. |
| 4      |  | Muestra una notificación de éxito. |
