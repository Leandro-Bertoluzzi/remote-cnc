from celery.result import AsyncResult
from components.TaskProgress import TaskProgress
from core.database.models import Task
from core.utils.storage import get_value_from_id
from PyQt5.QtWidgets import QLabel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from components.cards.TaskCard import TaskCard   # pragma: no cover


class TaskLabel(QLabel):
    def __init__(self, task: Task, taskProgress: TaskProgress, parent: 'TaskCard'):
        super(TaskLabel, self).__init__(parent)

        # Set desciption
        task_id = task.id
        task_name = task.name
        task_status_db = task.status
        description = f'Tarea {task_id}: {task_name}\nEstado: {task_status_db}'
        taskProgress.setVisible(False)

        # Check if it has a worker task ID
        task_worker_id = get_value_from_id('task', task.id)
        if not task_worker_id:
            self.setText(description)
            return

        # Get status in worker
        task_state: AsyncResult = AsyncResult(task_worker_id)
        task_info = task_state.info
        task_status = task_state.status

        if task_status == 'PROGRESS':
            sent_lines = task_info.get('sent_lines')
            processed_lines = task_info.get('processed_lines')
            total_lines = task_info.get('total_lines')

            description = (
                f'Tarea {task_id}: {task_name}\n'
                f'Estado: {task_status_db}\n'
            )

            taskProgress.set_total(total_lines)
            taskProgress.set_progress(sent_lines, processed_lines)
            taskProgress.setVisible(True)

        if task_status == 'FAILURE':
            error_msg = task_info
            description = (
                f'Tarea {task_id}: {task_name}\nEstado: {task_status_db} (FAILED)\n'
                f'Error: {error_msg}'
            )

        self.setText(description)
