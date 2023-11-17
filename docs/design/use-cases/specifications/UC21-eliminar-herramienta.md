| **Caso de uso**      | **Eliminar herramienta** |
| :---        | :---        |
| **Identificador**      | UC21 |
| **Actores**      | Administrador |
| **Precondición**   | -- |
| **Resultado**   | El usuario puede eliminar una herramienta/cabezal del registro. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda eliminar una herramienta/cabezal del registro.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En la vista de "Inventario", selecciona una herramienta. |  |
| 2      | Cliquea el botón "Eliminar". |  |
| 3      |  | Despliega una ventana de confirmación. |
| 4      | Presiona "Aceptar". |  |
| 5      |  | Actualiza la DB y muestra una notificación de éxito. |

**Curso alternativo (el usuario se retracta):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 4a      | Presiona "Cancelar". |  |
| 4b      |  | Cierra el mensaje de confirmación. |
