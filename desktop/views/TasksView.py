from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from config import USER_ID
import core.cncworker.utils as worker
from core.cncworker.workerStatusManager import WorkerStoreAdapter
from core.database.base import Session as SessionLocal
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.taskRepository import TaskRepository
from core.database.repositories.toolRepository import ToolRepository
from views.BaseListView import BaseListView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainWindow import MainWindow   # pragma: no cover


class TasksView(BaseListView):
    def __init__(self, parent: 'MainWindow'):
        super(TasksView, self).__init__(parent)

        try:
            self.getAssets()
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

    def getAssets(self):
        db_session = SessionLocal()
        files_repository = FileRepository(db_session)
        materials_repository = MaterialRepository(db_session)
        tools_repository = ToolRepository(db_session)

        self.files = [
            {
                'id': file.id,
                'name': file.file_name
            } for file in files_repository.get_all_files_from_user(USER_ID)
        ]
        self.materials = [
            {
                'id': material.id,
                'name': material.name
            } for material in materials_repository.get_all_materials()
        ]
        self.tools = [
            {
                'id': tool.id,
                'name': tool.name
            } for tool in tools_repository.get_all_tools()
        ]
