| **Caso de uso**      | **Eliminar usuario** |
| :---        | :---        |
| **Identificador**      | UC16 |
| **Actores**      | Administrador |
| **Precondición**   | El usuario está autenticado y tiene permisos de administrador.<br />Hay al menos un usuario. |
| **Resultado**   | El usuario puede eliminar a otro usuario. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda eliminar un usuario.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "administrar usuarios", selecciona un usuario. |  |
| 2      | Cliquea el botón "Eliminar". |  |
| 3      |  | Despliega una ventana de confirmación. |
| 4      | Presiona "Aceptar". |  |
| 5      |  | Notifica al servidor y muestra una notificación de éxito. |