| **Caso de uso**      | **Login, identificación de usuario** |
| :---        | :---        |
| **Identificador**      | UC01 |
| **Actores**      | Usuario |
| **Precondición**   | El usuario tiene nombre y contraseña válidos.<br />El usuario tiene acceso al sistema. |
| **Resultado**   | El usuario es autenticado y tiene acceso al sistema.<br />El usuario es redirigido a la página principal. |

**Resumen:**
Este caso de uso describe los pasos necesarios para que el usuario ingrese al sistema.

**Curso normal (básico):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 1      | Accede a la página de autenticación (login). |  |
| 2      |  | Muestra el formulario de ingreso. |
| 3      | Ingresa usuario y contraseña. |  |
| 5      |  | Habilita el botón de "login". |
| 6      | Cliquea el botón de "login". |  |
| 7      |  | Verifica la identidad del usuario. |
| 8      |  | Redirige a la página principal. |

**Curso alternativos (error de credenciales):**

| **N**      | **Acción realizada por actor** | **Acción realizada por el sistema** |
| :---        | :---        | :---        |
| 6a      |  | No se logra verificar la identidad del usuario. |
| 6b      |  | Se muestra un mensaje de error y se solicita revisar los datos ingresados. |