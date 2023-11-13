from PyQt5.QtWidgets import QWidget, QGridLayout, QToolBar, QToolButton
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.ButtonGrid import ButtonGrid
from components.ButtonList import ButtonList
from components.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.Terminal import Terminal

class ControlView(QWidget):
    def __init__(self, parent=None):
        super(ControlView, self).__init__(parent)

        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

        # VIEW STRUCTURE

        status_monitor = ControllerStatus(parent=self)
        controller_commands = ButtonGrid(['Home', 'Configurar', 'Modo chequeo', 'Desactivar alarma'], width=3, parent=self)
        controller_macros = ButtonList(['Sonda Z', 'Buscar centro', 'Cambiar herramienta', 'Dibujar círculo'], parent=self)
        controller_jog = ButtonGrid([' ↖ ', ' ↑ ', ' ↗ ', ' ← ', '', ' → ', ' ↙ ', ' ↓ ', ' ↘ '], width=3, parent=self)
        control_panel = ControllerActions(
            [
                (controller_commands, 'Acciones'),
                (controller_macros, 'Macros'),
                (controller_jog, 'Jog'),
            ],
            parent=self
        )
        code_editor = CodeEditor(self)
        terminal = Terminal(self)

        ############################################
        # 0                  |                     #
        # 1      STATUS      |     CODE_EDITOR     #
        # 2                  |                     #
        #   ---------------- | ------------------- #
        # 3  CONTROL_PANEL   |      TERMINAL       #
        #   -------------------------------------- #
        # 4               BTN_BACK                 #
        ############################################

        self.addToolBar()
        self.layout.addWidget(status_monitor, 0, 0, 3, 1)
        self.layout.addWidget(code_editor, 0, 1, 3, 1)
        self.layout.addWidget(control_panel, 3, 0)
        self.layout.addWidget(terminal, 3, 1)

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.backToMenu), 5, 0, 1, 2, alignment=Qt.AlignCenter)

    def addToolBar(self):
        """Adds a tool bar to the Main window
        """
        self.tool_bar = QToolBar()

        options = ['Nuevo', 'Abrir', 'Guardar', 'Conectar', 'Ejecutar', 'Detener', 'Pausar']
        for option in options:
            tool_button = QToolButton()
            tool_button.setText(option)
            tool_button.setCheckable(True)
            self.tool_bar.addWidget(tool_button)
        self.parent().addToolBar(Qt.TopToolBarArea, self.tool_bar)

    def backToMenu(self):
        """Removes the tool bar from the main window and goes back to the main menu
        """
        self.parent().removeToolBar(self.tool_bar)
        self.parent().backToMenu()
