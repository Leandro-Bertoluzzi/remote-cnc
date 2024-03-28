from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QGridLayout, QToolBar, QToolButton, QWidget
from components.buttons.MenuButton import MenuButton
from components.ControllerStatus import ControllerStatus
from components.text.LogsViewer import LogsViewer
from core.grbl.types import Status
from helpers.cncWorkerMonitor import CncWorkerMonitor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class MonitorView(QWidget):
    def __init__(self, parent: 'MainWindow'):
        super(MonitorView, self).__init__(parent)

        # STATE MANAGEMENT
        self.device_busy = CncWorkerMonitor.is_worker_running()

        # UI
        self.setup_ui()

        # GRBL/WORKER SYNC
        # self.grbl_sync = ?

        # Start monitors
        self.logs_viewer.start_watching()

    def setup_ui(self):
        """ Setup UI
        """
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.status_monitor = ControllerStatus(parent=self)
        self.logs_viewer = LogsViewer(parent=self)

        ############################################
        # 0                  |                     #
        # 1      STATUS      |                     #
        # 2                  |        LOGS         #
        #   ---------------- |                     #
        # 3        XXX       |                     #
        #   -------------------------------------- #
        # 4               BTN_BACK                 #
        ############################################

        self.createToolBars()
        layout.addWidget(self.status_monitor, 0, 0, Qt.AlignTop)
        if not self.device_busy:
            self.status_monitor.setEnabled(False)
        layout.addWidget(self.logs_viewer, 0, 1)

        layout.addWidget(
            MenuButton('Volver al menú', onClick=self.backToMenu),
            5, 0, 1, 2,
            alignment=Qt.AlignCenter
        )

    def getWindow(self) -> 'MainWindow':
        return self.parent()    # type: ignore

    def createToolBars(self):
        """Adds the tool bars to the Main window
        """
        self.tool_bar_log = QToolBar()
        self.tool_bar_log.setMovable(False)
        self.getWindow().addToolBar(Qt.TopToolBarArea, self.tool_bar_log)

        file_options = [
            ('Ver logs', lambda: None),
            ('Exportar', lambda: None),
            ('Pausar', self.pause_logs),
        ]

        for (label, action) in file_options:
            tool_button = QToolButton()
            tool_button.setText(label)
            tool_button.clicked.connect(action)
            self.tool_bar_log.addWidget(tool_button)

    def backToMenu(self):
        self.getWindow().removeToolBar(self.tool_bar_log)
        self.logs_viewer.stop()
        self.getWindow().backToMenu()

    def closeEvent(self, event: QCloseEvent):
        self.logs_viewer.stop()
        return super().closeEvent(event)

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

    def pause_logs(self):
        self.logs_viewer.toggle_paused()
