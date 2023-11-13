from PyQt5.QtWidgets import QWidget, QGridLayout, QToolBar, QToolButton, QComboBox
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from containers.ButtonGrid import ButtonGrid
from containers.ButtonList import ButtonList
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.Terminal import Terminal
from core.utils.serial import SerialService

class ControlView(QWidget):
    def __init__(self, parent=None):
        super(ControlView, self).__init__(parent)

        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

        # VIEW STRUCTURE

        self.status_monitor = ControllerStatus(parent=self)
        controller_commands = ButtonGrid(['Home', 'Configurar', 'Modo chequeo', 'Desactivar alarma'], width=3, parent=self)
        controller_macros = ButtonList(['Sonda Z', 'Buscar centro', 'Cambiar herramienta', 'Dibujar círculo'], parent=self)
        controller_jog = ButtonGrid([' ↖ ', ' ↑ ', ' ↗ ', ' ← ', '', ' → ', ' ↙ ', ' ↓ ', ' ↘ '], width=3, parent=self)
        self.control_panel = ControllerActions(
            [
                (controller_commands, 'Acciones'),
                (controller_macros, 'Macros'),
                (controller_jog, 'Jog'),
            ],
            parent=self
        )
        self.code_editor = CodeEditor(self)
        self.terminal = Terminal(self)

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
        self.layout.addWidget(self.status_monitor, 0, 0, 3, 1)
        self.layout.addWidget(self.code_editor, 0, 1, 3, 1)
        self.layout.addWidget(self.control_panel, 3, 0)
        self.layout.addWidget(self.terminal, 3, 1)

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.backToMenu), 5, 0, 1, 2, alignment=Qt.AlignCenter)

    def addToolBar(self):
        """Adds a tool bar to the Main window
        """
        self.tool_bar = QToolBar()

        options = [
            ('Nuevo', self.code_editor.new_file),
            ('Abrir', self.code_editor.open_file),
            ('Guardar', self.code_editor.save_file),
            ('Ejecutar', self.empty),
            ('Detener', self.empty),
            ('Pausar', self.empty),
            ('Conectar', self.empty),
        ]

        for (label, action) in options:
            tool_button = QToolButton()
            tool_button.setText(label)
            tool_button.clicked.connect(action)
            tool_button.setCheckable(True)
            self.tool_bar.addWidget(tool_button)

        # Connected devices
        combo_ports = QComboBox()
        ports = [port.name for port in SerialService.get_ports()]
        combo_ports.addItems(ports)
        self.tool_bar.addWidget(combo_ports)

        self.parent().addToolBar(Qt.TopToolBarArea, self.tool_bar)

    def backToMenu(self):
        """Removes the tool bar from the main window and goes back to the main menu
        """
        self.parent().removeToolBar(self.tool_bar)
        self.parent().backToMenu()

    def empty(self):
        pass
