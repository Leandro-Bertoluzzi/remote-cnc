| **Caso de uso**      | **Monitorear equipo** |
| :---        | :---        |
| **Identificador**      | UC25 |
| **Actores**      | Administrador |
| **Precondición**   | -- |
| **Resultado**   | El usuario puede ver el estado actual del equipo y un registro de actividad. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda monitorear el equipo, a través de un listado de registros de actividad (comandos enviados, mensajes recibidos, conexiones/desconexiones, etc) y, si el equipo está en ejecución, la posición y estado actual del mismo.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Monitoreo". |  |
| 2      |  | Consulta el estado del controlador de GRBL. |
| 3      |  | Muestra al usuario el estado del controlador. |
| 4      |  | Lee el archivo de registros del controlador de GRBL. |
| 5      |  | Muestra al usuario el listado de registros. |

**Curso alternativo (dispositivo desconectado):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Muestra el mensaje "Dispositivo desconectado". |

**Curso alternativo (no hay registros):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 5a      |  | Muestra el mensaje "No hay registros". |
