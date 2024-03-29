from components.StatusBar import StatusBar
from helpers.cncWorkerMonitor import CncWorkerMonitor
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QCloseEvent
from views.MainMenu import MainMenu


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setCentralWidget(MainMenu(self))
        self.setWindowTitle("CNC admin")
        self.setStyleSheet("background-color:#666666;")

        # CNC tasks monitor
        self.worker_monitor = CncWorkerMonitor()

        # UI components
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

        # Initial status
        self.status_bar.updateWorkerStatus('DESCONECTADO')
        self.status_bar.updateDeviceStatus('---')
        if CncWorkerMonitor.is_worker_on():
            self.status_bar.updateDeviceStatus('HABILITADO')
            self.status_bar.updateWorkerStatus('CONECTADO')
            if CncWorkerMonitor.is_worker_running():
                self.status_bar.updateDeviceStatus('TRABAJANDO...')

    # Navigation

    def changeView(self, widget):
        self.centralWidget().deleteLater()
        self.setCentralWidget(widget(self))

    def backToMenu(self):
        self.setCentralWidget(MainMenu(self))

    # Events

    def closeEvent(self, event: QCloseEvent):
        confirmation = QMessageBox.question(
            self,
            'Cerrar aplicación',
            '¿Realmente desea cerrar la aplicación?',
            QMessageBox.Yes | QMessageBox.Cancel
        )

        if confirmation == QMessageBox.Yes:
            self.centralWidget().closeEvent(event)
            event.accept()
        else:
            event.ignore()

    # Slots

    def on_task_finished(self):
        self.status_bar.updateDeviceStatus('DESHABILITADO')
        self.status_bar.setEnableBtnVisible(True)
        QMessageBox.information(
            self,
            'Tarea finalizada',
            '¡La tarea programada fue finalizada con éxito!\n'
            'Antes de poder ejecutar otra tarea, deberá preparar '
            'el área de trabajo y habilitar el equipo',
            QMessageBox.Ok
        )

    def on_task_failed(self, error_msg: str):
        self.status_bar.updateDeviceStatus('ERROR')
        QMessageBox.critical(
            self,
            'Tarea interrumpida',
            'Se encontró un error durante la ejecución de la tarea programada\n\n'
            'Detalle del error:\n'
            f'{error_msg}',
            QMessageBox.Ok
        )

    # Other methods

    def startWorkerMonitor(self, task_worker_id: str):
        self.status_bar.updateDeviceStatus('TRABAJANDO...')
        self.worker_monitor.start_task_monitor(task_worker_id)
        self.worker_monitor.task_finished.connect(self.on_task_finished)
        self.worker_monitor.task_failed.connect(self.on_task_failed)
        self.status_bar.setTemporalStatusMessage('Iniciado el monitor del worker')

    def enable_device(self):
        self.worker_monitor.set_device_enabled(True)
        self.status_bar.setEnableBtnVisible(False)
        self.status_bar.updateDeviceStatus('HABILITADO')
