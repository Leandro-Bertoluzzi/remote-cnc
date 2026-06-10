from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent, QResizeEvent, QShowEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

from desktop.app_context import AppContext
from desktop.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.components.StatusBar import StatusBar
from desktop.helpers.connectionErrors import get_friendly_error_message
from desktop.helpers.gatewayMonitor import GatewayMonitor
from desktop.views.BaseView import BaseView
from desktop.views.MainMenu import MainMenu


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext, parent=None):
        super(MainWindow, self).__init__(parent)

        self._context = context

        # Initial view and window setup
        self.setCentralWidget(MainMenu(self))
        self.setWindowTitle("CNC admin")
        self.setStyleSheet("background-color:#666666;")

        # CNC tasks monitor
        self.gateway_monitor = GatewayMonitor(self._context.gateway, self._context.logger)

        # UI components
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)
        self.initialized = 0

        # Initial status — wrapped to survive broker/Redis being offline
        self._refresh_worker_status()

        # Signals and slots
        self.gateway_monitor.file_finished.connect(self._on_task_finished)
        self.gateway_monitor.file_failed.connect(self._on_task_failed)

    # Worker status

    def _refresh_worker_status(self) -> None:
        """Query Gateway for current status, gracefully handling connection failures."""
        self.status_bar.updateWorkerStatus("DESCONECTADO")
        self.status_bar.updateDeviceStatus("---")

        try:
            if not self._context.device_service.is_worker_connected():
                return

            self.status_bar.updateWorkerStatus("CONECTADO")

            if not self._context.device_service.is_gateway_running():
                self.status_bar.updateDeviceStatus("GATEWAY OFFLINE")
            elif self._context.device_service.is_worker_busy():
                self.status_bar.updateDeviceStatus("TRABAJANDO...")
            else:
                self.status_bar.updateDeviceStatus("DISPONIBLE")
        except Exception:
            self._context.logger.warning("Could not reach worker/Redis — starting in offline mode")
            self.status_bar.setTemporalStatusMessage(
                "No se pudo conectar con el worker, iniciando en modo offline...", 5000
            )

    # UI

    def adjustWindowSize(self) -> None:
        # Available space in screen
        desktop = QApplication.desktop()
        if desktop is None:
            return
        available = desktop.availableGeometry()

        # Calculate frame size (window title and borders)
        frame_width = self.frameGeometry().width() - self.width()
        frame_height = self.frameGeometry().height() - self.height()

        # Size of window in full screen
        width = available.width() - frame_width
        height = available.height() - frame_height

        # Limit size to full screen
        self.setMaximumSize(width, height)

    # Navigation

    def changeView(self, widget):
        old_widget = self.centralWidget()
        try:
            new_widget = widget(self, context=self._context, gateway_monitor=self.gateway_monitor)
        except Exception as error:
            self._context.logger.warning("Error creating view %s: %s", widget.__name__, error)
            error_msg = get_friendly_error_message(error)
            error_widget = ConnectionErrorWidget(
                error_msg,
                retry_callback=lambda: self.changeView(widget),
                back_callback=self.backToMenu,
            )
            old_widget.deleteLater()
            self.setCentralWidget(error_widget)
            return
        self._connect_view_signals(new_widget)

        if hasattr(new_widget, "setup_toolbars"):
            new_widget.setup_toolbars()

        old_widget.deleteLater()
        self.setCentralWidget(new_widget)

    def _connect_view_signals(self, view: BaseView) -> None:
        """Connect standard view signals to MainWindow slots."""
        view.back_requested.connect(self.backToMenu)
        view.toolbar_added.connect(self._on_toolbar_added)
        view.toolbar_removed.connect(self._on_toolbar_removed)
        view.task_dispatched.connect(self._on_task_dispatched)

    def backToMenu(self):
        self.setCentralWidget(MainMenu(self))

    # Events

    def closeEvent(self, a0: QCloseEvent) -> None:
        confirmation = QMessageBox.question(
            self,
            "Cerrar aplicación",
            "¿Realmente desea cerrar la aplicación?",
            QMessageBox.Yes | QMessageBox.Cancel,
        )

        if confirmation == QMessageBox.Yes:
            self.centralWidget().closeEvent(a0)
            a0.accept()
        else:
            a0.ignore()

    def resizeEvent(self, a0: QResizeEvent) -> None:
        super().resizeEvent(a0)

        if self.initialized == 1:
            self.adjustWindowSize()
            self.initialized = 40

        if self.initialized == 0:
            self.initialized = 1

    def showEvent(self, a0: QShowEvent) -> None:
        self.showMaximized()

    # Slots

    def _on_task_finished(self):
        self.status_bar.updateDeviceStatus("DISPONIBLE")
        QMessageBox.information(
            self,
            "Tarea finalizada",
            "¡La tarea programada fue finalizada con éxito!",
            QMessageBox.Ok,
        )

    def _on_task_failed(self, error_msg: str):
        self.status_bar.updateDeviceStatus("ERROR")
        QMessageBox.critical(
            self,
            "Tarea interrumpida",
            "Se encontró un error durante la ejecución de la tarea programada\n\n"
            "Detalle del error:\n"
            f"{error_msg}",
            QMessageBox.Ok,
        )

    def _on_toolbar_added(self, toolbar):
        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def _on_toolbar_removed(self, toolbar):
        self.removeToolBar(toolbar)

    def _on_task_dispatched(self):
        """Start the worker monitor when a task is dispatched, and update status bar."""
        self.status_bar.updateDeviceStatus("TRABAJANDO...")
        self.gateway_monitor.start_monitor()
        self.status_bar.setTemporalStatusMessage("Iniciado el monitor del worker")
