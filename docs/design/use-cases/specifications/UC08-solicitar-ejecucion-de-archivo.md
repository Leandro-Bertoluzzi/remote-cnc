| **Caso de uso**      | **Solicitar ejecución de archivo** |
| :---        | :---        |
| **Identificador**      | UC08 |
| **Actores**      | Usuario |
| **Precondición**   | El usuario está autenticado y tiene acceso al sistema. |
| **Resultado**   | El usuario puede solicitar la ejecución de un archivo en el listado de archivos almacenados. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda solicitar la ejecución de uno de los archivos almacenados en el servidor.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "archivos", selecciona el archivo deseado. |  |
| 2      | Cliquea "solicitar ejecución". |  |
| 3      |  | Despliega una ventana de registro de solicitud. |
| 4      | Completa con un comentario y acepta. |  |
| 5      |  | Notifica al servidor y muestra una notificación de éxito. |

**Curso alternativo (eliminar archivo después de usar):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      | Tilda la opción "eliminar después de ejecutar". |  |