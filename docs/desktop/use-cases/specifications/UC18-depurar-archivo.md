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
| 12      |  | Inicia un nuevo hilo (thread) de ejecución. |
| 13      |  | **Mientras haya líneas en el archivo o se alcance breakpoint:** |
| 13.1      |  | Envía el comando por puerto serie para su ejecución. |
| 14      |  | Cierra el archivo y detiene el hilo de ejecución. |
| 15      |  | Habilita el uso del editor de código. |

**Curso alternativo (el archivo tiene modificaciones sin guardar):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 6      | Modifica el archivo. |  |
| 7      | Selecciona el puerto serie del equipo y presiona "Conectar". |  |
| 8      |  | Inicia la comunicación por puerto serie con el equipo. |
| 9      |  | Habilita el uso del panel de control y el terminal. |
| 10      | Presiona la opción "Ejecutar" en la barra de tareas. |  |
| 11      |  | Muestra una ventana emergente informando que debe guardar, o descartar, los cambios en el archivo. |

**Curso alternativo (se detiene la ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 13.1a      | Envía señal de "detener". |  |
| 13.1b      |  | Cierra el archivo y detiene el hilo de ejecución. |

**Curso alternativo (se pausa la ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 13.1a      | Envía señal de "pausar". |  |
| 13.1b      |  | (nada, sigue validando hasta que se retome la ejecución) |

**Curso alternativo (el buffer de GRBL está lleno):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 13.1a      |  | (nada, sigue validando hasta que el buffer tenga espacio) |

**Curso alternativo (hay un error durante la ejecución):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 13.1a      |  | Muestra una ventana emergente notificando el error. |
| 13.1b      |  | Pausa el envío del archivo. |
