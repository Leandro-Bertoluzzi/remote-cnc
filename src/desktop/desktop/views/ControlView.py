"""Control View — Direct CNC control through the Gateway.

Provides an interactive UI for:

* Connecting to the CNC Gateway (session-based)
* Jogging, homing, alarm reset, check-mode
* Sending ad-hoc G-code commands via the Terminal
* Streaming a G-code file for execution
* Real-time status monitoring via PubSub

All communication goes through ``GatewayClient`` → Redis queues → CNC Gateway.
No direct serial access.  See DR-0001 for technical rationale.
"""

import logging
from typing import TYPE_CHECKING

from core.utilities.gateway.constants import ACTION_PAUSE, ACTION_RESUME
from core.utilities.gateway.gatewayClient import GatewayClient
from core.utilities.grbl.types import ParserState, Status
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QGridLayout

from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.CodeEditor import CodeEditor
from desktop.components.ControllerStatus import ControllerStatus
from desktop.components.dialogs.AbsoluteMoveDialog import AbsoluteMoveDialog
from desktop.components.Joystick import Joystick
from desktop.components.Terminal import Terminal
from desktop.components.ToolBar import ToolBar, ToolBarOptionInfo
from desktop.containers.ButtonGrid import ButtonGrid
from desktop.containers.ControllerActions import ControllerActions
from desktop.helpers.gatewayMonitor import GatewayMonitor
from desktop.services.deviceService import DeviceService
from desktop.views.BaseView import BaseView

if TYPE_CHECKING:
    from desktop.MainWindow import MainWindow  # pragma: no cover

logger = logging.getLogger(__name__)

# User ID used for ad-hoc sessions from the Desktop's ControlView.
_DESKTOP_USER_ID = 0
_DESKTOP_CLIENT_TYPE = "desktop_control"

# Heartbeat interval in milliseconds (renew session TTL periodically).
_HEARTBEAT_INTERVAL_MS = 60_000

GRBL_STATUS_DISCONNECTED: Status = {
    "activeState": "disconnected",
    "mpos": {"x": 0.0, "y": 0.0, "z": 0.0},
    "wpos": {"x": 0.0, "y": 0.0, "z": 0.0},
    "ov": [0, 0, 0],
    "wco": {"x": 0.0, "y": 0.0, "z": 0.0},
}


class ControlView(BaseView):
    def __init__(self, parent: "MainWindow"):
        super(ControlView, self).__init__(parent)

        # STATE MANAGEMENT
        self.connected = False
        self.session_id: str | None = None
        self._gateway = GatewayClient()
        self._file_running = False
        self._file_paused = False

        try:
            self.device_busy = DeviceService.is_worker_busy()
        except Exception:
            logger.warning("Could not check worker status — assuming idle")
            self.device_busy = False

        self.setup_ui()

        # GATEWAY SYNC — status via PubSub
        self.gateway_sync = GatewayMonitor()
        self.gateway_sync.new_status.connect(self.update_device_status)
        self.gateway_sync.new_message.connect(self.write_to_terminal)
        self.gateway_sync.file_progress.connect(self.update_file_progress)
        self.gateway_sync.file_finished.connect(self.finished_file_execution)
        self.gateway_sync.file_failed.connect(self.failed_file_execution)

        # HEARTBEAT TIMER
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(_HEARTBEAT_INTERVAL_MS)
        self._heartbeat_timer.timeout.connect(self._renew_session)

    # SETUP METHODS

    def setup_ui(self):
        """Setup UI"""
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.status_monitor = ControllerStatus(parent=self)
        controller_commands = ButtonGrid(
            [
                ("Home", self.run_homing_cycle),
                # TODO: Enable configure_grbl once the Gateway supports query responses
                ("Configurar GRBL", self.configure_grbl),
                # TODO: Habilitar modo chequeo sólo en estado IDLE
                ("Modo chequeo", self.toggle_check_mode),
                # TODO: Habilitar desactivación de alarma sólo en estado ALARM
                ("Desactivar alarma", self.disable_alarm),
                ("Mover a", self.move_absolute),
            ],
            parent=self,
        )
        controller_macros = ButtonGrid(
            [
                ("Sonda Z", lambda: None),
                ("Buscar centro", lambda: None),
                ("Cambiar herramienta", lambda: None),
                ("Dibujar círculo", lambda: None),
            ],
            parent=self,
        )
        controller_jog = Joystick(parent=self)
        controller_jog.set_jog_callback(self._send_jog)
        self.control_panel = ControllerActions(
            [
                (controller_commands, "Acciones"),
                (controller_macros, "Macros"),
                (controller_jog, "Jog"),
            ],
            parent=self,
        )
        self.code_editor = CodeEditor(self)
        self.terminal = Terminal(parent=self)
        self.terminal.command_submitted.connect(self._send_command)

        self.enable_controls(False)

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
            MenuButton("Volver al menú", onClick=self.backToMenu),
            2,
            0,
            1,
            2,
            alignment=Qt.AlignCenter,
        )

    def __del__(self):
        self.disconnect_device()

    def createToolBars(self):
        """Adds the tool bars to the Main window"""
        file_options: list[ToolBarOptionInfo] = [
            ("Nuevo", self.code_editor.new_file, False),
            ("Importar", self.code_editor.import_file, False),
            ("Exportar", self.code_editor.export_file, False),
        ]
        self.tool_bar_files = ToolBar(file_options, self.getWindow(), self)

        if self.device_busy:
            return

        exec_options: list[ToolBarOptionInfo] = [
            ("Ejecutar", self.start_file_execution, False),
            ("Detener", self.stop_file_execution, False),
            ("Pausar", self.toggle_pause, True),
            ("Conectar", self.toggle_connected, True),
        ]
        self.tool_bar_grbl = ToolBar(exec_options, self.getWindow(), self)
        self.pause_button = self.tool_bar_grbl.get_options()["pausar"]
        self.connect_button = self.tool_bar_grbl.get_options()["conectar"]

    # EVENTS

    def backToMenu(self):
        """Removes the tool bar from the main window and goes back to the main menu"""
        self.disconnect_device()
        self.getWindow().removeToolBar(self.tool_bar_files)
        if not self.device_busy:
            self.getWindow().removeToolBar(self.tool_bar_grbl)
        self.getWindow().backToMenu()

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.disconnect_device()
        return super().closeEvent(a0)

    # SESSION / CONNECTION

    def toggle_connected(self):
        """Acquire or release the Gateway session."""
        if self.connected:
            self.disconnect_device()
            return
        self.connect_device()

    def connect_device(self):
        """Acquire a Gateway session and start status monitoring."""
        if self.connected:
            return

        try:
            session_id = self._gateway.acquire_session(_DESKTOP_USER_ID, _DESKTOP_CLIENT_TYPE)
        except Exception as error:
            self.connect_button.setChecked(False)
            self.showError("Error de conexión", str(error))
            return

        if session_id is None:
            self.connect_button.setChecked(False)
            self.showError(
                "Sesión ocupada",
                "No se pudo adquirir la sesión — otro cliente está conectado",
            )
            return

        self.session_id = session_id
        self.connected = True
        self.connect_button.setText("Desconectar")
        self.enable_controls(True)

        # Start real-time status sync + heartbeat
        self.gateway_sync.start_monitor()
        self._heartbeat_timer.start()

    def disconnect_device(self):
        """Release the Gateway session and stop monitoring."""
        if not self.connected:
            return

        # Release session
        if self.session_id:
            try:
                self._gateway.release_session(self.session_id)
            except Exception as error:
                self.showError("Error", str(error))
                return

        self.session_id = None
        self.connected = False
        self._file_running = False
        self._file_paused = False

        try:
            self.gateway_sync.stop_monitor()
            self._heartbeat_timer.stop()
            self.connect_button.setText("Conectar")
            self.enable_controls(False)
            self.status_monitor.set_status(GRBL_STATUS_DISCONNECTED)
        except RuntimeError:
            pass

    def enable_controls(self, enable: bool = True):
        self.status_monitor.setEnabled(enable)
        self.control_panel.setEnabled(enable)
        self.terminal.setEnabled(enable)

    # HEARTBEAT

    def _renew_session(self):
        """Periodically renew the Gateway session TTL."""
        if not self.session_id:
            return
        try:
            renewed = self._gateway.renew_session(self.session_id)
        except Exception:
            renewed = False

        if not renewed:
            self.disconnect_device()
            self.showError(
                "Sesión perdida",
                "La sesión con el Gateway expiró o fue tomada por otro cliente",
            )

    # GATEWAY COMMAND SENDERS

    def _send_command(self, command: str) -> None:
        """Send a G-code command via the Gateway (connected to Terminal signal)."""
        if self.session_id:
            self._gateway.send_command(self.session_id, command)

    def _send_jog(self, x, y, z, feedrate, units, distance_mode) -> None:
        """Send a jog command via the Gateway (passed as callback to JogController)."""
        if self.session_id:
            self._gateway.send_jog(
                self.session_id,
                x,
                y,
                z,
                feedrate,
                units=units,
                distance_mode=distance_mode,
            )

    # GRBL ACTIONS (sent as G-code commands through the Gateway)

    def run_homing_cycle(self):
        self._send_command("$H")
        self.showWarning("Homing", "Iniciando ciclo de home")

    def disable_alarm(self):
        self._send_command("$X")

    def toggle_check_mode(self):
        self._send_command("$C")
        self.showInfo(
            "Modo de prueba",
            "Se envió el comando para alternar el modo de prueba",
        )

    def configure_grbl(self):
        # TODO: Implement once the Gateway supports query-response for settings.
        self.showWarning(
            "No disponible",
            "La configuración de GRBL no está disponible en el modo remoto.\n"
            "Esta funcionalidad será implementada en una futura versión.",
        )

    # FILE EXECUTION (delegated to Gateway)

    def start_file_execution(self):
        file_path = self.code_editor.get_file_path()

        if not file_path:
            self.showWarning(
                "Cambios sin guardar", "Por favor guarde el archivo antes de continuar"
            )
            return

        if self.code_editor.get_modified():
            self.showWarning(
                "Cambios sin guardar",
                "El archivo tiene cambios sin guardar en el editor, por favor guárdelos",
            )
            return

        if not self.session_id:
            self.showError("Sin sesión", "Debe conectarse al Gateway antes de ejecutar un archivo")
            return

        self.code_editor.setReadOnly(True)
        self.code_editor.resetProcessedLines()
        self._file_running = True
        self._file_paused = False

        self._gateway.request_file_execution(self.session_id, file_path)

    def toggle_pause(self):
        """Pause or resume the running G-code file via Gateway realtime commands."""
        if not self.session_id:
            return

        if self._file_paused:
            self._gateway.send_realtime(self.session_id, ACTION_RESUME)
            self._file_paused = False
            self.pause_button.setText("Pausar")
        else:
            self._gateway.send_realtime(self.session_id, ACTION_PAUSE)
            self._file_paused = True
            self.pause_button.setText("Retomar")

    def stop_file_execution(self):
        if not self.session_id:
            return
        self._gateway.request_file_stop(self.session_id)
        self.code_editor.setReadOnly(False)
        self._file_running = False
        self._file_paused = False

    # Interaction with other widgets

    def move_absolute(self):
        dialog = AbsoluteMoveDialog(parent=self)
        dialog.set_jog_callback(self._send_jog)

        if not dialog.exec():
            return

        dialog.make_absolute_move()

    # SLOTS

    def write_to_terminal(self, text):
        self.terminal.display_text(text)

    def update_device_status(self, status: Status, parserstate: ParserState):
        self.status_monitor.set_status(status)
        self.status_monitor.set_feedrate(parserstate["feedrate"])
        self.status_monitor.set_spindle(parserstate["spindle"])
        self.status_monitor.set_tool(parserstate["tool"])

    def update_file_progress(self, sent_lines: int, processed_lines: int, total_lines: int):
        """Update the code editor with file-execution progress from the Gateway."""
        self.code_editor.markProcessedLines(sent_lines)

    def finished_file_execution(self):
        self.code_editor.setReadOnly(False)
        self._file_running = False
        self._file_paused = False
        self.showInfo(
            "Archivo finalizado",
            "El archivo fue ejecutado exitosamente.",
        )

    def failed_file_execution(self, error_message: str):
        self.code_editor.setReadOnly(False)
        self._file_running = False
        self._file_paused = False
        self.showError(
            "Error en ejecución",
            f"{error_message}. Por favor, resuelva el error y reinicie la ejecución.",
        )
