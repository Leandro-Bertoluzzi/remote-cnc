| **Caso de uso**      | **Depurar archivo** |
| :---        | :---        |
| **Identificador**      | UC18 |
| **Actores**      | Administrador |
| **Precondición**   | El usuario tiene seleccionado un archivo. |
| **Resultado**   | El usuario puede depurar manualmente el archivo seleccionado. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda depurar un archivo manualmente, ejecutando los comandos del mismo línea por línea mientras monitorea el avance.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | Entre las opciones del archivo, selecciona la opción "depurar". |  |
| 2      |  | Muestra al usuario la vista de depuración de archivo, con el código en un editor con capacidad de colocar breakpoints y ejecutar línea por línea. |
| 3      | Sobre una de las líneas del código, selecciona la opción de "ejecutar" comando |  |
| 4      |  | Deshabilita los controles, muestra un ícono de carga y envía el comando por puerto serie para su ejecución. |
| 5      |  | Se espera hasta recibir notificación de ejecución del comando. |
| 6      |  | Se actualiza el indicador de coordenadas del cabezal y se habilitan los controles. |
| 7      | Coloca un marcador de "breakpoint" en una de las líneas del archivo y presiona el botón "ejecutar". |  |
| 8      |  | Deshabilita los controles, muestra un ícono de carga y comienza a enviar los comandos por puerto serie para su ejecución. |
| 9      |  | Se espera hasta recibir notificación de ejecución de cada comando. |
| 10      |  | Se actualiza el indicador de coordenadas del cabezal por cada comando ejecutado. |
| 11      |  | Una vez ejecutados todos los comandos, se habilitan los controles. |

**Curso alternativo (comando inválido):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 10a      |  | Se notifica que el comando a ejecutar es inválido.  |
| 10b      |  | Señala en el archivo la línea en la que se produjo el error. |

**Curso alternativo (colisión detectada):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 10a      |  | Se notifica que la ejecución del comando escapa a las dimensiones del equipo. |
| 10b      |  | Señala en el archivo la línea en la que se produjo el error. |
