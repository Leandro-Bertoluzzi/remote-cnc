from config import USER_ID
from components.cards.Card import Card
from components.dialogs.TaskCancelDialog import TaskCancelDialog, FROM_REJECT
from core.database.base import Session as SessionLocal
from core.database.models import Task, TASK_APPROVED_STATUS, TASK_REJECTED_STATUS
from core.database.repositories.taskRepository import TaskRepository
from helpers.cncWorkerMonitor import CncWorkerMonitor
from helpers.utils import needs_confirmation, send_task_to_worker


class RequestCard(Card):
    def __init__(self, task: Task, parent=None):
        super(RequestCard, self).__init__(parent)

        self.task = task
        self.setup_ui()

    def setup_ui(self):
        description = f'Tarea {self.task.id}: {self.task.name}\nUsuario: {self.task.user.name}'
        self.setDescription(description)

        self.addButton("Aprobar", self.approveTask)
        self.addButton("Rechazar", self.rejectTask)

    @needs_confirmation('¿Realmente desea aprobar la solicitud?', 'Aprobar solicitud')
    def approveTask(self):
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.update_task_status(self.task.id, TASK_APPROVED_STATUS, USER_ID)
            if not CncWorkerMonitor.is_device_available():
                self.getView().refreshLayout()
                return

            self.runTask()
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.getView().refreshLayout()

    @needs_confirmation(
        '¿Desea ejecutar la tarea ahora? En caso contrario, '
        'puede ejecutarla manualmente en cualquier momento.',
        'Ejecutar tarea'
    )
    def runTask(self):
        worker_task_id = send_task_to_worker(self.task.id)
        self.getWindow().startWorkerMonitor(worker_task_id)
        self.showInformation(
            'Tarea enviada',
            'Se envió la tarea al equipo para su ejecución'
        )

    def rejectTask(self):
        rejectDialog = TaskCancelDialog(origin=FROM_REJECT)
        if not rejectDialog.exec():
            return

        reject_reason = rejectDialog.getInput()
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.update_task_status(
                self.task.id,
                TASK_REJECTED_STATUS,
                USER_ID,
                reject_reason
            )
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.getView().refreshLayout()
