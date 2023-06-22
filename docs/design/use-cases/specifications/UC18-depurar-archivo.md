| **Caso de uso**      | **Depurar archivo** |
| :---        | :---        |
| **Identificador**      | UC18 |
| **Actores**      | Administrador |
| **Precondición**   | El usuario está autenticado y tiene permisos de administrador.<br />El usuario tiene seleccionado un archivo. |
| **Resultado**   | El usuario puede depurar manualmente el archivo seleccionado. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que un administrador pueda depurar un archivo manualmente, ejecutando los comandos del mismo línea por línea mientras monitorea el avance.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | Entre las opciones del archivo, selecciona la opción "depurar". |  |
| 2      |  | Muestra al usuario la vista de depuración de archivo, con el código en un editor con capacidad de colocar breakpoints y ejecutar línea por línea. |
| 3      | Sobre una de las líneas del código, selecciona la opción de "ejecutar" comando |  |
| 4      |  | Deshabilita los controles, muestra un ícono de carga y notifica al servidor. |
| 5      |  | El servidor notifica que se finalizó la acción. |
| 6      |  | Se actualiza el indicador de coordenadas del cabezal y se habilitan los controles. |
| 7      | Coloca un marcador de "breakpoint" en una de las líneas del archivo y presiona el botón "ejecutar". |  |
| 8      |  | Deshabilita los controles, muestra un ícono de carga y notifica al servidor. |
| 9      |  | El servidor retorna las coordenadas del cabezal actualizadas por cada comando ejecutado. |
| 10      |  | Se actualiza el indicador de coordenadas del cabezal. |
| 11      |  | El servidor notifica que se finalizó la acción. |
| 12      |  | Se actualiza el indicador de coordenadas del cabezal y se habilitan los controles. |

**Curso alternativo (comando inválido):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 11a      |  | El servidor notifica que el comando a ejecutar es inválido.  |
| 11b      |  | Señala en el archivo la línea en la que se produjo el error. |

**Curso alternativo (colisión detectada):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 11a      |  | El servidor notifica que la ejecución del comando escapa a las dimensiones del equipo. |
| 11b      |  | Señala en el archivo la línea en la que se produjo el error. |