from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QSizePolicy, QSpacerItem
from components.buttons.MenuButton import MenuButton
from components.ControllerStatus import ControllerStatus
from components.TaskProgress import TaskProgress
import core.worker.utils as worker
from core.grbl.types import Status, ParserState
from typing import TYPE_CHECKING
from views.BaseView import BaseView

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class MonitorView(BaseView):
    def __init__(self, parent: 'MainWindow'):
        super(MonitorView, self).__init__(parent)

        # STATE MANAGEMENT
        self.device_busy = worker.is_worker_running()

        # UI
        self.setup_ui()

        # GRBL/WORKER SYNC
        self.connect_worker()

    # SETUP METHODS

    def setup_ui(self):
        """Setup UI
        """
        layout = QGridLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.status_monitor = ControllerStatus(parent=self)
        self.task_progress = TaskProgress(parent=self)

        ############################################
        # 0      STATUS      |                     #
        #   ---------------- |                     #
        # 1     PROGRESS     |                     #
        #   ---------------- |                     #
        # 2                  |                     #
        #   -------------------------------------- #
        # 3               BTN_BACK                 #
        ############################################

        layout.addWidget(self.status_monitor, 0, 0, 1, 1, Qt.AlignTop)
        layout.addWidget(self.task_progress, 1, 0, 1, 1)
        if not self.device_busy:
            self.status_monitor.setEnabled(False)
            self.task_progress.setEnabled(False)

        self.placeholder = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(self.placeholder, 2, 0)

        layout.addWidget(
            MenuButton('Volver al menú', onClick=self.backToMenu),
            5, 0, 1, 2,
            alignment=Qt.AlignCenter
        )

    def connect_worker(self):
        """Synchronizes the status monitor with the CNC worker.
        """
        if self.device_busy:
            self.getWindow().worker_monitor.task_new_status.connect(self.update_task_status)

    # EVENTS

    def backToMenu(self):
        self.getWindow().backToMenu()

    # UI METHODS

    def update_task_status(
        self,
        sent_lines: int,
        processed_lines: int,
        total_lines: int,
        controller_status: Status,
        grbl_parserstate: ParserState
    ):
        self.task_progress.set_total(total_lines)
        self.task_progress.set_progress(sent_lines, processed_lines)

        self.update_device_status(
            controller_status,
            grbl_parserstate['feedrate'],
            grbl_parserstate['spindle'],
            grbl_parserstate['tool']
        )

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
