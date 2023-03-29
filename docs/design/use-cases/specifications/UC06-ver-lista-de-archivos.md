| **Caso de uso**      | **Ver archivos almacenados** |
| :---        | :---        |
| **Identificador**      | UC06 |
| **Actores**      | Usuario |
| **Precondición**   | El usuario está autenticado y tiene acceso al sistema.<br />Hay archivos almacenados en el servidor. |
| **Resultado**   | El usuario puede ver un listado de archivos almacenados y de acceso público. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda ver un listado de los archivos que decidió almacenar en el servidor, y aquellos disponibles para todos los usuarios.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "archivos". |  |
| 2      |  | Solicita al servidor el listado de archivos disponibles para el usuario actual. |
| 3      |  | Muestra al usuario el listado de archivos. |