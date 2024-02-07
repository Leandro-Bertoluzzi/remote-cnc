from PyQt5.QtWidgets import QComboBox, QGridLayout, QMessageBox, QToolBar, QToolButton, QWidget
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.dialogs.GrblConfigurationDialog import GrblConfigurationDialog
from containers.ButtonGrid import ButtonGrid
from containers.ButtonList import ButtonList
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.JogController import JogController
from components.Terminal import Terminal
from config import SERIAL_BAUDRATE
from core.database.base import Session as SessionLocal
from core.database.models import TASK_IN_PROGRESS_STATUS
from core.database.repositories.taskRepository import TaskRepository
from core.grbl.grblController import GrblController
from core.grbl.types import GrblSettings
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
        self.device_settings: GrblSettings = {}
        self.device_busy = True
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            self.device_busy = repository.are_there_tasks_with_status(TASK_IN_PROGRESS_STATUS)
        except Exception as error:
            QMessageBox.critical(
                self,
                'Error de base de datos',
                str(error),
                QMessageBox.Ok
            )

        # GRBL CONTROLLER CONFIGURATION
        grbl_logger = logging.getLogger('control_view_logger')
        grbl_logger.setLevel(logging.INFO)
        self.grbl_controller = GrblController(grbl_logger)
        self.checkmode = self.grbl_controller.getCheckModeEnabled()

        # VIEW STRUCTURE
        self.status_monitor = ControllerStatus(self.grbl_controller, parent=self)
        controller_commands = ButtonGrid([
            ('Home', self.run_homing_cycle),
            ('Ver configuración', self.query_device_settings),
            ('Configurar GRBL', self.configure_grbl),
            # TODO: Habilitar modo chequeo sólo en estado IDLE
            ('Modo chequeo', self.toggle_check_mode),
            # TODO: Habilitar desactivación de alarma sólo en estado ALARM
            ('Desactivar alarma', self.disable_alarm),
        ], width=3, parent=self)
        controller_macros = ButtonList([
            ('Sonda Z', self.empty),
            ('Buscar centro', self.empty),
            ('Cambiar herramienta', self.empty),
            ('Dibujar círculo', self.empty),
        ], parent=self)
        controller_jog = JogController(self.grbl_controller, parent=self)
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

        self.createToolBars()
        panel_row = 0
        if not self.device_busy:
            self.layout.addWidget(self.status_monitor, 0, 0, 3, 1)
            panel_row = 3
        self.layout.addWidget(self.code_editor, 0, 1, 3, 1)
        self.layout.addWidget(self.control_panel, panel_row, 0)
        self.layout.addWidget(self.terminal, 3, 1)

        self.layout.addWidget(
            MenuButton('Volver al menú', onClick=self.backToMenu),
            5, 0, 1, 2,
            alignment=Qt.AlignCenter
        )

    def __del__(self):
        if not self.device_busy:
            self.disconnect_device()

    def createToolBars(self):
        """Adds the tool bars to the Main window
        """
        self.tool_bar_files = QToolBar()
        self.tool_bar_files.setMovable(False)
        self.parent().addToolBar(Qt.TopToolBarArea, self.tool_bar_files)

        file_options = [
            ('Nuevo', self.code_editor.new_file),
            ('Importar', self.code_editor.import_file),
            ('Exportar', self.code_editor.export_file),
        ]

        for (label, action) in file_options:
            tool_button = QToolButton()
            tool_button.setText(label)
            tool_button.clicked.connect(action)
            self.tool_bar_files.addWidget(tool_button)

        if self.device_busy:
            return

        self.tool_bar_grbl = QToolBar()
        self.tool_bar_grbl.setMovable(False)
        self.parent().addToolBar(Qt.TopToolBarArea, self.tool_bar_grbl)

        exec_options = [
            ('Ejecutar', self.empty),
            ('Detener', self.empty),
            ('Pausar', self.empty),
        ]

        for (label, action) in exec_options:
            tool_button = QToolButton()
            tool_button.setText(label)
            tool_button.clicked.connect(action)
            self.tool_bar_grbl.addWidget(tool_button)

        self.connect_button = QToolButton()
        self.connect_button.setText('Conectar')
        self.connect_button.clicked.connect(self.toggle_connected)
        self.connect_button.setCheckable(True)
        self.tool_bar_grbl.addWidget(self.connect_button)

        # Connected devices
        combo_ports = QComboBox()
        combo_ports.addItems([''])
        ports = [port.device for port in SerialService.get_ports()]
        combo_ports.addItems(ports)
        combo_ports.currentTextChanged.connect(self.set_selected_port)
        self.tool_bar_grbl.addWidget(combo_ports)

    def backToMenu(self):
        """Removes the tool bar from the main window and goes back to the main menu
        """
        self.parent().removeToolBar(self.tool_bar_files)
        if not self.device_busy:
            self.parent().removeToolBar(self.tool_bar_grbl)
        self.parent().backToMenu()

    def set_selected_port(self, port):
        self.port_selected = port

    def toggle_connected(self):
        """Open or close the connection with the GRBL device.
        """
        if self.connected:
            self.disconnect_device()
            return

        self.connect_device()

    def connect_device(self):
        """Open the connection with the GRBL device connected to the selected port.
        """
        if not self.port_selected:
            self.connect_button.setChecked(False)
            return

        if self.connected:
            return

        response = {}
        try:
            response = self.grbl_controller.connect(self.port_selected, SERIAL_BAUDRATE)
        except Exception as error:
            QMessageBox.critical(
                self,
                'Error',
                str(error),
                QMessageBox.Ok
            )
            return

        self.connect_button.setText('Desconectar')
        self.connected = True
        self.enable_serial_widgets(True)
        self.status_monitor.start_monitor()
        self.write_to_terminal(response['raw'])

    def disconnect_device(self):
        """Close the connection with the GRBL device.
        """
        if not self.connected:
            return

        try:
            self.grbl_controller.disconnect()
        except Exception as error:
            QMessageBox.critical(
                self,
                'Error',
                str(error),
                QMessageBox.Ok
            )
            return
        self.connect_button.setText('Conectar')
        self.connected = False
        self.enable_serial_widgets(False)
        self.status_monitor.stop_monitor()
        self.status_monitor.set_status(GRBL_STATUS_DISCONNECTED)

    def enable_serial_widgets(self, enable: bool = True):
        self.status_monitor.setEnabled(enable)
        self.control_panel.setEnabled(enable)
        self.terminal.setEnabled(enable)

    # GRBL Actions

    def query_device_settings(self, show_in_terminal=True):
        self.device_settings = self.grbl_controller.getGrblSettings()

        if not show_in_terminal:
            return

        for key, setting in self.device_settings.items():
            self.write_to_terminal(f"{key}={setting['value']}")

    def run_homing_cycle(self):
        self.grbl_controller.handleHomingCycle()

        QMessageBox.warning(
            self,
            'Homing',
            "Iniciando ciclo de home",
            QMessageBox.Ok
        )

    def disable_alarm(self):
        self.grbl_controller.disableAlarm()

    def toggle_check_mode(self):
        self.grbl_controller.toggleCheckMode()

        # Update internal state
        self.checkmode = not self.checkmode
        QMessageBox.information(
            self,
            'Modo de prueba',
            f"El modo de prueba fue {'activado' if self.checkmode else 'desactivado'}",
            QMessageBox.Ok
        )

    # Interaction with other widgets

    def configure_grbl(self):
        self.query_device_settings(False)
        configurationDialog = GrblConfigurationDialog(self.device_settings)

        if configurationDialog.exec():
            settings = configurationDialog.getModifiedInputs()
            if not settings:
                return

            self.grbl_controller.setSettings(settings)

            QMessageBox.information(
                self,
                'Configuración de GRBL',
                '¡La configuración de GRBL fue actualizada correctamente!',
                QMessageBox.Ok
            )

    def write_to_terminal(self, text):
        self.terminal.display_text(text)

    def empty(self):
        pass
