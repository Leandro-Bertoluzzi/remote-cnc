from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QComboBox, QGridLayout, QToolBar, QToolButton
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
from core.grbl.grblController import GrblController
from core.grbl.types import GrblSettings, Status
from core.utils.serial import SerialService
from helpers.cncWorkerMonitor import CncWorkerMonitor
from helpers.fileSender import FileSender
from helpers.grblSync import GrblSync
import logging
from typing import TYPE_CHECKING
from views.BaseView import BaseView

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover

GRBL_STATUS_DISCONNECTED: Status = {
    'activeState': 'disconnected',
    'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'ov': [0, 0, 0],
    'wco': {'x': 0.0, 'y': 0.0, 'z': 0.0}
}


class ControlView(BaseView):
    def __init__(self, parent: 'MainWindow'):
        super(ControlView, self).__init__(parent)

        # STATE MANAGEMENT
        self.connected = False
        self.port_selected = ''
        self.device_settings: GrblSettings = {}
        self.device_busy = CncWorkerMonitor.is_worker_running()

        self.setup_grbl_controller()
        self.setup_ui()

        # GRBL SYNC
        self.grbl_sync = GrblSync(self)

        # FILE SENDER
        self.file_sender = FileSender(self)

    def setup_grbl_controller(self):
        """ Setup GRBL controller
        """
        grbl_logger = logging.getLogger('control_view_logger')
        grbl_logger.setLevel(logging.INFO)
        self.grbl_controller = GrblController(grbl_logger)
        self.checkmode = self.grbl_controller.getCheckModeEnabled()

    def setup_ui(self):
        """ Setup UI
        """
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.status_monitor = ControllerStatus(parent=self)
        controller_commands = ButtonGrid([
            ('Home', self.run_homing_cycle),
            ('Configurar GRBL', self.configure_grbl),
            # TODO: Habilitar modo chequeo sólo en estado IDLE
            ('Modo chequeo', self.toggle_check_mode),
            # TODO: Habilitar desactivación de alarma sólo en estado ALARM
            ('Desactivar alarma', self.disable_alarm),
        ], width=3, parent=self)
        controller_macros = ButtonList([
            ('Sonda Z', lambda: None),
            ('Buscar centro', lambda: None),
            ('Cambiar herramienta', lambda: None),
            ('Dibujar círculo', lambda: None),
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
            layout.addWidget(self.status_monitor, 0, 0, 3, 1)
            panel_row = 3
        layout.addWidget(self.code_editor, 0, 1, 3, 1)
        layout.addWidget(self.control_panel, panel_row, 0)
        layout.addWidget(self.terminal, 3, 1)

        layout.addWidget(
            MenuButton('Volver al menú', onClick=self.backToMenu),
            5, 0, 1, 2,
            alignment=Qt.AlignCenter
        )

    def __del__(self):
        self.disconnect_device()

    def closeEvent(self, event: QCloseEvent):
        self.disconnect_device()
        return super().closeEvent(event)

    def createToolBars(self):
        """Adds the tool bars to the Main window
        """
        self.tool_bar_files = QToolBar()
        self.tool_bar_files.setMovable(False)
        self.getWindow().addToolBar(Qt.TopToolBarArea, self.tool_bar_files)

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
        self.getWindow().addToolBar(Qt.TopToolBarArea, self.tool_bar_grbl)

        exec_options = [
            ('Ejecutar', self.start_file_stream),
            ('Detener', self.stop_file_stream),
            ('Pausar', self.pause_file_stream),
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
        self.disconnect_device()
        self.getWindow().removeToolBar(self.tool_bar_files)
        if not self.device_busy:
            self.getWindow().removeToolBar(self.tool_bar_grbl)
        self.getWindow().backToMenu()

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
            self.showError('Error', str(error))
            return

        self.connect_button.setText('Desconectar')
        self.connected = True
        self.enable_serial_widgets(True)
        self.grbl_sync.start_monitor()
        self.write_to_terminal(response['raw'])

    def disconnect_device(self):
        """Close the connection with the GRBL device.
        """
        if not self.connected:
            return

        try:
            self.grbl_controller.disconnect()
        except Exception as error:
            self.showError('Error', str(error))
            return
        self.connected = False
        self.file_sender.stop()
        self.grbl_sync.stop_monitor()
        try:
            self.connect_button.setText('Conectar')
            self.enable_serial_widgets(False)
            self.status_monitor.set_status(GRBL_STATUS_DISCONNECTED)
        except RuntimeError:
            pass

    def enable_serial_widgets(self, enable: bool = True):
        self.status_monitor.setEnabled(enable)
        self.control_panel.setEnabled(enable)
        self.terminal.setEnabled(enable)

    # GRBL Actions

    def query_device_settings(self):
        self.device_settings = self.grbl_controller.getGrblSettings()

    def run_homing_cycle(self):
        self.grbl_controller.handleHomingCycle()
        self.showWarning('Homing', "Iniciando ciclo de home")

    def disable_alarm(self):
        self.grbl_controller.disableAlarm()

    def toggle_check_mode(self):
        self.grbl_controller.toggleCheckMode()

        # Update internal state
        self.checkmode = not self.checkmode
        self.showInfo(
            'Modo de prueba',
            f"El modo de prueba fue {'activado' if self.checkmode else 'desactivado'}"
        )

    def start_file_stream(self):
        file_path = self.code_editor.get_file_path()

        if not file_path:
            self.showWarning(
                'Cambios sin guardar',
                'Por favor guarde el archivo antes de continuar'
            )
            return

        # Check if the file has changes without saving
        if self.code_editor.get_modified():
            self.showWarning(
                'Cambios sin guardar',
                'El archivo tiene cambios sin guardar en el editor, por favor guárdelos'
            )
            return

        self.code_editor.setReadOnly(True)
        self.code_editor.resetProcessedLines()
        self.file_sender.set_file(file_path)
        self.file_sender.resume()
        self.file_sender.start()

    def pause_file_stream(self):
        self.file_sender.toggle_paused()

    def stop_file_stream(self):
        self.code_editor.setReadOnly(False)
        self.file_sender.stop()

    def finished_file_stream(self):
        self.code_editor.setReadOnly(False)
        self.showInfo(
            'Archivo enviado',
            'Se terminó de enviar el archivo para su ejecución, por favor espere a que termine'
        )

    # Interaction with other widgets

    def configure_grbl(self):
        self.query_device_settings()
        configurationDialog = GrblConfigurationDialog(self.device_settings)

        if not configurationDialog.exec():
            return

        settings = configurationDialog.getModifiedInputs()
        if not settings:
            return

        self.grbl_controller.setSettings(settings)
        self.showInfo(
            'Configuración de GRBL',
            '¡La configuración de GRBL fue actualizada correctamente!'
        )

    def write_to_terminal(self, text):
        self.terminal.display_text(text)

    def update_device_status(
            self,
            status: Status,
            feedrate: float,
            spindle: float,
            tool_index: int
    ):
        self.status_monitor.set_status(status)
        self.status_monitor.set_feedrate(feedrate)
        self.status_monitor.set_spindle(spindle)
        self.status_monitor.set_tool(tool_index)

    def update_already_read_lines(self, count: int):
        self.code_editor.markProcessedLines(count)
