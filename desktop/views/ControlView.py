from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QComboBox, QGridLayout
from PyQt5.QtCore import Qt
from components.buttons.MenuButton import MenuButton
from components.dialogs.GrblConfigurationDialog import GrblConfigurationDialog
from components.dialogs.AbsoluteMoveDialog import AbsoluteMoveDialog
from containers.ButtonGrid import ButtonGrid
from containers.ControllerActions import ControllerActions
from components.CodeEditor import CodeEditor
from components.ControllerStatus import ControllerStatus
from components.Joystick import Joystick
from components.Terminal import Terminal
from components.ToolBar import ToolBar
from config import SERIAL_BAUDRATE
from core.grbl.grblController import GrblController
from core.grbl.types import GrblSettings, ParserState, Status
from core.utils.serial import SerialService
from helpers.cncWorkerMonitor import CncWorkerMonitor
from helpers.fileStreamer import FileStreamer
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
        self.grbl_sync = GrblSync(self.grbl_controller)
        self.grbl_sync.new_message.connect(self.write_to_terminal)
        self.grbl_sync.new_status.connect(self.update_device_status)
        self.grbl_sync.failed.connect(self.failed_command)
        self.grbl_sync.finished.connect(self.finished_command)

        # FILE SENDER
        self.file_streamer = FileStreamer(self.grbl_controller)
        self.file_streamer.sent_line.connect(self.update_already_read_lines)
        self.file_streamer.finished.connect(self.finished_file_stream)

    # SETUP METHODS

    def setup_grbl_controller(self):
        """ Setup GRBL controller
        """
        grbl_logger = logging.getLogger('control_view_logger')
        grbl_logger.setLevel(logging.INFO)
        self.grbl_controller = GrblController(grbl_logger)
        self.grbl_status = self.grbl_controller.grbl_status
        self.checkmode = self.grbl_status.is_checkmode()

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
            ('Mover a', self.move_absolute),
        ], parent=self)
        controller_macros = ButtonGrid([
            ('Sonda Z', lambda: None),
            ('Buscar centro', lambda: None),
            ('Cambiar herramienta', lambda: None),
            ('Dibujar círculo', lambda: None),
        ], parent=self)
        controller_jog = Joystick(self.grbl_controller, parent=self)
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
        # 0      STATUS      |     CODE_EDITOR     #
        #   ---------------- | ------------------- #
        # 1  CONTROL_PANEL   |      TERMINAL       #
        #   -------------------------------------- #
        # 2               BTN_BACK                 #
        ############################################

        self.createToolBars()
        panel_row = 0
        if not self.device_busy:
            layout.addWidget(self.status_monitor, 0, 0)
            panel_row = 1
        layout.addWidget(self.code_editor, 0, 1)
        layout.addWidget(self.control_panel, panel_row, 0)
        layout.addWidget(self.terminal, 1, 1)

        layout.addWidget(
            MenuButton('Volver al menú', onClick=self.backToMenu),
            2, 0, 1, 2,
            alignment=Qt.AlignCenter
        )

    def __del__(self):
        self.disconnect_device()

    def createToolBars(self):
        """Adds the tool bars to the Main window
        """
        file_options = [
            ('Nuevo', self.code_editor.new_file, False),
            ('Importar', self.code_editor.import_file, False),
            ('Exportar', self.code_editor.export_file, False),
        ]
        self.tool_bar_files = ToolBar(file_options, self.getWindow(), self)

        if self.device_busy:
            return

        exec_options = [
            ('Ejecutar', self.start_file_stream, False),
            ('Detener', self.stop_file_stream, False),
            ('Pausar', self.pause_file_stream, True),
            ('Conectar', self.toggle_connected, True),
        ]
        self.tool_bar_grbl = ToolBar(exec_options, self.getWindow(), self)
        self.pause_button = self.tool_bar_grbl.get_options()['pausar']
        self.connect_button = self.tool_bar_grbl.get_options()['conectar']

        # Connected devices
        combo_ports = QComboBox()
        combo_ports.addItems([''])
        ports = [port.device for port in SerialService.get_ports()]
        combo_ports.addItems(ports)
        combo_ports.currentTextChanged.connect(self.set_selected_port)
        self.tool_bar_grbl.addWidget(combo_ports)

    # EVENTS

    def backToMenu(self):
        """Removes the tool bar from the main window and goes back to the main menu
        """
        self.disconnect_device()
        self.getWindow().removeToolBar(self.tool_bar_files)
        if not self.device_busy:
            self.getWindow().removeToolBar(self.tool_bar_grbl)
        self.getWindow().backToMenu()

    def closeEvent(self, event: QCloseEvent):
        self.disconnect_device()
        return super().closeEvent(event)

    # SERIAL PORT ACTIONS

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
            self.connect_button.setChecked(False)
            self.showError('Error', str(error))
            return

        self.connect_button.setText('Desconectar')
        self.connected = True
        self.enable_serial_widgets(True)
        self.write_to_terminal(response['raw'])

        # Configure GRBL sync
        self.grbl_sync.start_monitor()

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

        try:
            self.file_streamer.stop()
            self.grbl_sync.stop_monitor()
            self.connect_button.setText('Conectar')
            self.enable_serial_widgets(False)
            self.status_monitor.set_status(GRBL_STATUS_DISCONNECTED)
        except RuntimeError:
            pass

    def enable_serial_widgets(self, enable: bool = True):
        self.status_monitor.setEnabled(enable)
        self.control_panel.setEnabled(enable)
        self.terminal.setEnabled(enable)

    # GRBL ACTIONS

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

    # FILE ACTIONS

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

        # Reset GRBL controller
        if not self.grbl_status.clear_error():
            self.showError(
                'Alarma activa',
                'Hay una alarma activa, debe desactivarla antes de continuar.'
            )
            return
        if self.grbl_status.paused():
            self.grbl_controller.setPaused(False)
        self.grbl_controller.restartCommandsCount()

        # Update code editor
        self.code_editor.setReadOnly(True)
        self.code_editor.resetProcessedLines()

        # Configure file sender
        self.file_streamer.set_file(file_path)
        self.file_streamer.start()

    def pause_file_stream(self):
        # Pause/Resume file streaming
        self.file_streamer.toggle_paused()

        # Pause/Resume GRBL controller
        paused = self.file_streamer.is_paused()
        self.pause_button.setText('Retomar' if paused else 'Pausar')
        self.grbl_controller.setPaused(paused)

    def stop_file_stream(self):
        self.code_editor.setReadOnly(False)
        self.file_streamer.stop()

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

    def move_absolute(self):
        dialog = AbsoluteMoveDialog(self.grbl_controller, parent=self)

        if not dialog.exec():
            return

        dialog.make_absolute_move()

    # SLOTS

    def write_to_terminal(self, text):
        self.terminal.display_text(text)

    def update_device_status(
            self,
            status: Status,
            parserstate: ParserState
    ):
        self.status_monitor.set_status(status)
        self.status_monitor.set_feedrate(parserstate['feedrate'])
        self.status_monitor.set_spindle(parserstate['spindle'])
        self.status_monitor.set_tool(parserstate['tool'])

    def update_already_read_lines(self, count: int):
        self.code_editor.markProcessedLines(count)

    def finished_file_stream(self):
        self.code_editor.setReadOnly(False)
        self.showInfo(
            'Archivo enviado',
            'Se terminó de enviar el archivo para su ejecución, por favor espere a que termine.'
        )

    def failed_command(self, error_message: str):
        self.file_streamer.pause()

        self.showError(
            'Error',
            f'{error_message}. Por favor, resuelva el error y reinicie la ejecución.'
        )

    def finished_command(self):
        """An "end of program" command was sent (M2, M30)
        """
        self.file_streamer.stop()
        self.finished_file_stream()
