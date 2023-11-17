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
| 1      | En el menú principal, selecciona la opción de "Control manual y calibración". |  |
| 2      | Presiona la opción "Abrir" en la barra de tareas. |  |
| 3      |  | Abre una ventana de selección de archivo. |
| 4      | Selecciona el archivo a cargar. |  |
| 5      |  | Muestra el contenido del archivo en el editor de código. |
| 6      | (opcional) Agrega uno o varios "breakpoints" al código. |  |
| 7      | Selecciona el puerto serie del equipo y presiona "Conectar". |  |
| 8      |  | Inicia la comunicación por puerto serie con el equipo. |
| 9      |  | Habilita el uso del panel de control y el terminal. |
| 10      | Presiona la opción "Ejecutar" en la barra de tareas. |  |
| 11      |  | Inhabilita el uso del editor de código. |
| 12      |  | **Mientras haya líneas en el archivo o se alcance breakpoint:** |
| 12.1      |  | Escribe el comando en el terminal, lo envía por puerto serie para su ejecución y espera hasta recibir notificación de ejecución del comando. |
| 12.2      |  | Se actualizan las coordenadas del cabezal en el monitor de estado y se muestra la respuesta del dispositivo en el terminal. |
| 13      |  | Habilita el uso del editor de código. |

**Curso alternativo (comando inválido):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 12.2a      |  | Se notifica que el comando a ejecutar es inválido.  |
| 12.2b      |  | Muestra una ventana emergente indicando que hubo un error. |
| 12.2c      | Cierra la ventana |  |
| 12.2d      |  | Habilita el uso del editor de código y señala en el archivo la línea en la que se produjo el error. |
