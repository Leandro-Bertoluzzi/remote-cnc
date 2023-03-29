| **Caso de uso**      | **Control manual** |
| :---        | :---        |
| **Identificador**      | UC10 |
| **Actores**      | Administrador |
| **Precondición**   | El usuario está autenticado y tiene permisos de administrador. |
| **Resultado**   | El usuario puede controlar el equipo de forma manual. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda controlar el equipo de forma manual, con fines de depuración o calibración del equipo; o validación de comandos/archivos.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | En el menú principal, selecciona la opción de "control manual". |  |
| 2      |  | Inicia un canal de comunicación bidireccional con el servidor. |
| 3      |  | Muestra al usuario la vista de control manual, con controles de dirección y entrada de código G. |
| 4      | Cliquea uno de los botones de dirección. |  |
| 5      |  | Deshabilita los controles, muestra un ícono de carga y notifica al servidor. |
| 6      |  | El servidor notifica que se finalizó la acción. |
| 7      |  | Se actualiza el indicador de coordenadas del cabezal y se habilitan los controles. |
| 8      | Indica la coordenada a la que debe desplazarse el cabezal. |  |
| 9      |  | Deshabilita los controles, muestra un ícono de carga y notifica al servidor. |
| 10      |  | El servidor notifica que se finalizó la acción. |
| 11      |  | Se actualiza el indicador de coordenadas del cabezal y se habilitan los controles. |
| 12      | Ingresa un comando de código G y cliquea el botón "ejecutar". |  |
| 13      |  | Deshabilita los controles, muestra un ícono de carga y notifica al servidor. |
| 14      |  | El servidor notifica que se finalizó la acción. |
| 15      |  | Se actualiza el indicador de coordenadas del cabezal y se habilitan los controles. |