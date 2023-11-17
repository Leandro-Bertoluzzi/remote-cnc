from PyQt5.QtWidgets import QComboBox, QGridLayout, QToolBar, QToolButton, QWidget
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from containers.ButtonGrid import ButtonGrid
from containers.ButtonList import ButtonList
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.JogController import JogController
from components.Terminal import Terminal
from core.config import SERIAL_BAUDRATE
from core.database.models.task import TASK_IN_PROGRESS_STATUS
from core.utils.database import get_tool_by_id, are_there_tasks_with_status
from core.grbl.grblController import GrblController
from core.utils.serial import SerialService
import logging

GRBL_STATUS_DISCONNECTED = {
    'activeState': 'disconnected',
    'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0}
}

class ControlView(QWidget):
    def __init__(self, parent=None):
        super(ControlView, self).__init__(parent)

        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)

        # STATE MANAGEMENT
        self.connected = False
        self.port_selected = ''
        self.device_settings = {}
        self.device_busy = are_there_tasks_with_status(TASK_IN_PROGRESS_STATUS)

        # GRBL CONTROLLER CONFIGURATION
        grbl_logger = logging.getLogger('control_view_logger')
        grbl_logger.setLevel(logging.INFO)
        self.grbl_controller = GrblController(grbl_logger)

        # VIEW STRUCTURE
        self.status_monitor = ControllerStatus(parent=self)
        controller_commands = ButtonGrid([
            ('Home', self.empty),
            ('Configurar', self.empty),
            ('Modo chequeo', self.empty),
            ('Desactivar alarma', self.empty),
        ], width=3, parent=self)
        controller_macros = ButtonList([
            ('Sonda Z', self.empty),
            ('Buscar centro', self.empty),
            ('Cambiar herramienta', self.empty),
            ('Dibujar círculo', self.empty),
        ], parent=self)
        controller_jog = JogController(self.grbl_controller, self.write_to_terminal, parent=self)
        self.control_panel = ControllerActions(
            [
                (controller_commands, 'Acciones'),
                (controller_macros, 'Macros'),
                (controller_jog, 'Jog'),
            ],
            parent=self
        )
        self.code_editor = CodeEditor(self)
        self.terminal = Terminal(self.grbl_controller, parent=self)

        self.enable_serial_widgets(False)

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
        if not self.device_busy:
            self.layout.addWidget(self.status_monitor, 0, 0, 3, 1)
        self.layout.addWidget(self.code_editor, 0, 1, 3, 1)
        self.layout.addWidget(self.control_panel, 3, 0)
        self.layout.addWidget(self.terminal, 3, 1)

        self.layout.addWidget(MenuButton('Volver al menú', onClick=self.backToMenu), 5, 0, 1, 2, alignment=Qt.AlignCenter)

    def addToolBar(self):
        """Adds a tool bar to the Main window
        """
        self.tool_bar = QToolBar()
        self.parent().addToolBar(Qt.TopToolBarArea, self.tool_bar)

        file_options = [
            ('Nuevo', self.code_editor.new_file),
            ('Abrir', self.code_editor.open_file),
            ('Guardar', self.code_editor.save_file),
        ]

        for (label, action) in file_options:
            tool_button = QToolButton()
            tool_button.setText(label)
            tool_button.clicked.connect(action)
            self.tool_bar.addWidget(tool_button)

        if self.device_busy:
            return

        exec_options = [
            ('Ejecutar', self.empty),
            ('Detener', self.empty),
            ('Pausar', self.empty),
        ]

        for (label, action) in exec_options:
            tool_button = QToolButton()
            tool_button.setText(label)
            tool_button.clicked.connect(action)
            self.tool_bar.addWidget(tool_button)

        self.connect_button = QToolButton()
        self.connect_button.setText('Conectar')
        self.connect_button.clicked.connect(self.connect_device)
        self.connect_button.setCheckable(True)
        self.tool_bar.addWidget(self.connect_button)

        # Connected devices
        combo_ports = QComboBox()
        combo_ports.addItems([''])
        ports = [port.device for port in SerialService.get_ports()]
        combo_ports.addItems(ports)
        combo_ports.currentTextChanged.connect(self.set_selected_port)
        self.tool_bar.addWidget(combo_ports)

    def backToMenu(self):
        """Removes the tool bar from the main window and goes back to the main menu
        """
        self.parent().removeToolBar(self.tool_bar)
        self.parent().backToMenu()

    def set_selected_port(self, port):
        self.port_selected = port

    def connect_device(self):
        """Open the connection with the GRBL device connected to the selected port.
        """
        if not self.port_selected:
            self.connect_button.setChecked(False)
            return

        if self.connected:
            self.grbl_controller.disconnect()
            self.connect_button.setText('Conectar')
            self.connected = False
            self.enable_serial_widgets(False)
            self.status_monitor.set_status(GRBL_STATUS_DISCONNECTED)
            return

        response = self.grbl_controller.connect(self.port_selected, SERIAL_BAUDRATE)
        self.connect_button.setText('Desconectar')
        self.connected = True
        self.enable_serial_widgets(True)
        self.query_device_status()
        self.write_to_terminal(response['raw'])

    def enable_serial_widgets(self, enable:bool = True):
        self.status_monitor.setEnabled(enable)
        self.control_panel.setEnabled(enable)
        self.terminal.setEnabled(enable)

    def query_device_status(self):
        status = self.grbl_controller.queryStatusReport()
        self.status_monitor.set_status(status)

        feedrate = self.grbl_controller.getFeedrate()
        self.status_monitor.set_feedrate(feedrate)

        spindle = self.grbl_controller.getSpindle()
        self.status_monitor.set_spindle(spindle)

        tool_index_grbl = self.grbl_controller.getTool()
        tool_info = get_tool_by_id(tool_index_grbl)
        self.status_monitor.set_tool(tool_index_grbl, tool_info)

    def query_device_settings(self):
        settings = self.grbl_controller.queryGrblSettings()
        self.device_settings = settings

    def write_to_terminal(self, text):
        self.terminal.display_text(text)

    def empty(self):
        pass
