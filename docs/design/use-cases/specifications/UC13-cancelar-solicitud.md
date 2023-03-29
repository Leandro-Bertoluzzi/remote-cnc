| **Caso de uso**      | **Cancelar solicitud de ejecución** |
| :---        | :---        |
| **Identificador**      | UC13 |
| **Actores**      | Administrador |
| **Precondición**   | El usuario está autenticado y tiene permisos de administrador.<br />Hay al menos una solicitud de ejecución de un usuario. |
| **Resultado**   | El usuario puede ver un listado de las solicitudes y rechazarlas. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda ver un listado de las solicitudes de ejecución de los usuarios y rechazarlas.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "solicitudes de ejecución", selecciona una de ellas. |  |
| 2      | Cliquea el botón de "Rechazar". |  |
| 3      |  | Muestra el formulario de cancelación de solicitud. |
| 4      | Completa la razón de cancelación y presiona el botón de "Aceptar". |  |
| 5      |  | Notifica al servidor y muestra una notificación de éxito. |