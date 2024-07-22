| **Caso de uso**      | **Almacenar nuevo archivo** |
| :---        | :---        |
| **Identificador**      | UC07 |
| **Actores**      | Usuario |
| **Precondición**   | -- |
| **Resultado**   | El usuario puede agregar un archivo al listado de archivos disponibles. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda agregar un archivo al listado de los archivos disponibles.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Archivos", cliquea el botón "Nuevo". |  |
| 2      |  | Muestra un modal con opciones para cargar el archivo. |
| 3      | Selecciona el archivo a cargar. |  |
| 4      | (opcional) Elige un nuevo nombre de archivo. |  |
| 5      | Presiona el botón "Aceptar". |  |
| 6      |  | Inicia la pantalla de carga y envía el archivo al sistema de archivos y la DB. |
| 7      |  | Muestra el mensaje de éxito. |
| 8      | Ve el nuevo archivo en el listado de archivos. |  |

**Curso alternativo (archivo inválido):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 7a      |  | Recibe la notificación de que el archivo tiene formato inválido. |
| 7b      |  | Muestra un mensaje informado al usuario del error y solicitando la validación del archivo |
