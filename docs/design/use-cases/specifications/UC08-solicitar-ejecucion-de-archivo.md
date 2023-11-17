| **Caso de uso**      | **Solicitar ejecución de archivo** |
| :---        | :---        |
| **Identificador**      | UC08 |
| **Actores**      | Usuario |
| **Precondición**   | Hay al menos un archivo, una herramienta y un material en la base de datos. |
| **Resultado**   | El usuario puede solicitar la ejecución de un archivo en el listado de archivos disponibles. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda solicitar la creación de una tarea a partir de la vista de archivos.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Archivos", selecciona el archivo deseado. |  |
| 2      | Cliquea "solicitar ejecución". |  |
| 3      |  | Despliega una ventana de registro de solicitud. |
| 4      | Completa el nombre, selecciona material y herramienta, y (opcional) agrega un comentario. |  |
| 5      | Presiona "Aceptar". |  |
| 6      |  | Actualiza la DB y muestra una notificación de éxito. |

**Curso alternativo (eliminar archivo después de usar):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      | Tilda la opción "eliminar después de ejecutar". |  |
