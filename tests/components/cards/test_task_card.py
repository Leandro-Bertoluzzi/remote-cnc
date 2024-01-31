import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from celery.result import AsyncResult
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from core.database.models import Task
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.taskRepository import TaskRepository
from core.database.repositories.toolRepository import ToolRepository
from views.TasksView import TasksView


class TestTaskCard:
    task = Task(
        user_id=1,
        file_id=1,
        tool_id=1,
        material_id=1,
        name='Example task'
    )

    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        mocker.patch.object(TasksView, 'refreshLayout')

        # Patch the DB methods
        mocker.patch.object(FileRepository, 'get_all_files_from_user', return_value=[])
        mocker.patch.object(ToolRepository, 'get_all_tools', return_value=[])
        mocker.patch.object(MaterialRepository, 'get_all_materials', return_value=[])

        self.parent = TasksView()
        self.task.id = 1

    def test_task_card_init(self, qtbot):
        card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(card)

        assert card.task == self.task
        assert card.layout is not None
        assert card.label_description.text() == 'Tarea 1: Example task\nEstado: pending_approval'

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_task_card_update_task(self, qtbot, mocker, dialogResponse, expected_updated):
        card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(card)

        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Updated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_task = mocker.patch.object(TaskRepository, 'update_task')

        # Call the updateTask method
        card.updateTask()

        # Validate DB calls
        assert mock_update_task.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_task_params = {
                'id': 1,
                'user_id': 1,
                'file_id': 2,
                'tool_id': 3,
                'material_id': 4,
                'name': 'Updated task',
                'note': 'Just a simple description',
                'priority': 0,
            }
            mock_update_task.assert_called_with(*update_task_params.values())

    def test_task_card_update_task_db_error(self, qtbot, mocker):
        card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(card)

        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Updated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_task = mocker.patch.object(
            TaskRepository,
            'update_task',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the updateTask method
        card.updateTask()

        # Validate DB calls
        assert mock_update_task.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_task_card_remove_task(self, qtbot, mocker, msgBoxResponse, expectedMethodCalls):
        card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(card)

        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_remove_task = mocker.patch.object(TaskRepository, 'remove_task')

        # Call the removeTask method
        card.removeTask()

        # Validate DB calls
        assert mock_remove_task.call_count == expectedMethodCalls

    def test_task_card_remove_task_db_error(self, qtbot, mocker):
        card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(card)

        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_task = mocker.patch.object(
            TaskRepository,
            'remove_task',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeTask method
        card.removeTask()

        # Validate DB calls
        assert mock_remove_task.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "status",
            [
                'pending_approval',
                'on_hold',
                'in_progress',
                'finished',
                'rejected',
                'cancelled'
            ]
        )
    def test_task_card_show_task_progress(self, qtbot, mocker, status):
        # Mock task status
        self.task.status = status

        # Mock Celery task metadata
        task_metadata = {
            'result': {
                'percentage': 50,
                'progress': 10,
                'total_lines': 20
            }
        }

        # Mock Celery methods
        mock_query_task = mocker.patch.object(
            AsyncResult,
            '__init__',
            return_value=None
        )
        mock_query_task_info = mocker.patch.object(
            AsyncResult,
            '_get_task_meta',
            return_value=task_metadata
        )

        # Instantiate card
        card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(card)

        # Assertions
        if status == 'in_progress':
            expected_text = 'Tarea 1: Example task\nEstado: in_progress\nProgreso: 10/20 (50%)'
            assert card.label_description.text() == expected_text
            assert mock_query_task.call_count == 1
            assert mock_query_task_info.call_count == 1
            return

        assert card.label_description.text() == f'Tarea 1: Example task\nEstado: {status}'
        assert mock_query_task.call_count == 0
        assert mock_query_task_info.call_count == 0
