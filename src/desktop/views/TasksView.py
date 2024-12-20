from desktop.components.cards.TaskCard import TaskCard
from desktop.components.dialogs.TaskDataDialog import TaskDataDialog
from desktop.config import USER_ID
import utilities.worker.utils as worker
from utilities.worker.workerStatusManager import WorkerStoreAdapter
from database.base import SessionLocal
from database.repositories.taskRepository import TaskRepository
from database.utils import get_assets
from desktop.views.BaseListView import BaseListView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class TasksView(BaseListView):
    def __init__(self, parent: 'MainWindow'):
        super(TasksView, self).__init__(parent)

        try:
            self.files, self.materials, self.tools = get_assets(USER_ID)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return

        self.setItemListFromValues(
            'TAREAS',
            'La cola de tareas está vacía',
            self.createTaskCard,
            'Crear tarea',
            self.createTask
        )
        self.refreshLayout()

    def createTaskCard(self, task):
        return TaskCard(
            task,
            self.device_available,
            self.files,
            self.tools,
            self.materials,
            parent=self
        )

    def getItems(self):
        db_session = SessionLocal()
        repository = TaskRepository(db_session)
        tasks = repository.get_all_tasks_from_user(USER_ID, status='all')

        # Check if there is a task in progress
        enabled = WorkerStoreAdapter.is_device_enabled()
        running = worker.is_worker_running()
        self.device_available = enabled and not running

        return tasks

    def createTask(self):
        taskDialog = TaskDataDialog(self.files, self.tools, self.materials)
        if not taskDialog.exec():
            return

        file_id, tool_id, material_id, name, note = taskDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = TaskRepository(db_session)
            repository.create_task(USER_ID, file_id, tool_id, material_id, name, note)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.refreshLayout()
