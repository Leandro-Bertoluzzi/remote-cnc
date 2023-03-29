| **Caso de uso**      | **Ver solicitudes de ejecución** |
| :---        | :---        |
| **Identificador**      | UC11 |
| **Actores**      | Administrador |
| **Precondición**   | El usuario está autenticado y tiene permisos de administrador.<br />Hay al menos una solicitud de ejecución de un usuario. |
| **Resultado**   | El usuario puede ver un listado de las solicitudes. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda ver un listado de las solicitudes de ejecución de los usuarios.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "solicitudes de ejecución". |  |
| 2      |  | Solicita al servidor el listado de solicitudes de ejecución. |
| 3      |  | Muestra al usuario el listado de solicitudes. |