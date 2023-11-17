| **Caso de uso**      | **Ver archivos almacenados** |
| :---        | :---        |
| **Identificador**      | UC06 |
| **Actores**      | Usuario |
| **Precondición**   | -- |
| **Resultado**   | El usuario puede ver un listado de archivos almacenados y de acceso público. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario pueda ver un listado de los archivos correspondientes a su usuario, y aquellos disponibles para todos los usuarios.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "Archivos". |  |
| 2      |  | Solicita a la DB el listado de archivos disponibles para el usuario actual. |
| 3      |  | Muestra al usuario el listado de archivos. |

**Curso alternativo (no hay archivos almacenados):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 3a      |  | Recibe un listado vacío de la DB. |
| 3b      |  | Muestra al usuario el mensaje "Aún no hay archivos almacenados". |
