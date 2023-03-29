| **Caso de uso**      | **Almacenar nuevo archivo en servidor** |
| :---        | :---        |
| **Identificador**      | UC07 |
| **Actores**      | Usuario |
| **Precondición**   | El usuario está autenticado y tiene acceso al sistema. |
| **Resultado**   | El usuario puede agregar un archivo al listado de archivos almacenados. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda agregar un archivo al listado de los archivos almacenados en el servidor.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "archivos", cliquea el botón "Nuevo". |  |
| 2      |  | Muestra un modal con opciones para cargar desde el equipo, desde una URL, etc. |
| 3      | Selecciona el método de carga del archivo. |  |
| 4      | Selecciona el archivo a cargar. |  |
| 5      | Presiona el botón "Aceptar". |  |
| 6      |  | Inicia la pantalla de carga y envía al servidor el archivo. |
| 7      |  | Muestra el mensaje de éxito/error de carga del archivo. |
| 8      | Ve el nuevo archivo en el listado de archivos. |  |

**Curso alternativo (archivo inválido):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 7a      |  | Recibe la notificación de que el archivo tiene formato inválido. |
| 7b      |  | Muestra un mensaje informado al usuario del error y solicitando la validación del archivo |