import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton
from celery.result import AsyncResult
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskCancelDialog import TaskCancelDialog
from components.dialogs.TaskDataDialog import TaskDataDialog
from core.database.models import Task, TASK_ON_HOLD_STATUS
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.taskRepository import TaskRepository
from core.database.repositories.toolRepository import ToolRepository
from helpers.cncWorkerMonitor import CncWorkerMonitor
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot
from typing import Union
from views.TasksView import TasksView


class TestTaskCard:
    task = Task(
        user_id=1,
        file_id=1,
        tool_id=1,
        material_id=1,
        name='Example task'
    )

    @pytest.fixture(scope='function')
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture, mock_window):
        mocker.patch.object(TasksView, 'refreshLayout')

        # Patch the DB methods
        mocker.patch.object(FileRepository, 'get_all_files_from_user', return_value=[])
        mocker.patch.object(ToolRepository, 'get_all_tools', return_value=[])
        mocker.patch.object(MaterialRepository, 'get_all_materials', return_value=[])

        # Mock card's auxiliary methods
        mocker.patch.object(TaskCard, 'check_task_status')

        # Mock parent widget
        self.window = mock_window
        self.parent = TasksView(self.window)

        # Create an instance of the card
        self.task.id = 1
        self.card = TaskCard(self.task, False, parent=self.parent)
        qtbot.addWidget(self.card)

    @pytest.mark.parametrize(
            "status,expected_buttons",
            [
                ('pending_approval', 2),
                ('on_hold', 2),
                ('in_progress', 0),
                ('finished', 1),
                ('rejected', 2),
                ('cancelled', 2)
            ]
        )
    def test_task_card_init(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        helpers,
        status,
        expected_buttons
    ):
        # Mock task status
        self.task.status = status
        self.task.id = 1

        # Mock card's auxiliary methods
        mock_set_task_description = mocker.patch.object(TaskCard, 'check_task_status')

        # Instantiate card
        card = TaskCard(self.task, False)
        qtbot.addWidget(card)

        # Assertions
        assert card.task == self.task
        assert card.layout() is not None
        assert helpers.count_widgets(card.layout_buttons, QPushButton) == expected_buttons
        assert mock_set_task_description.call_count == 1

    def test_task_card_init_device_busy(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock task status
        self.task.status = TASK_ON_HOLD_STATUS
        self.task.id = 1

        # Mock card's auxiliary methods
        mocker.patch.object(TaskCard, 'check_task_status')

        # Instantiate card
        card = TaskCard(self.task, True)
        qtbot.addWidget(card)

        # Assertions
        while card.layout().count():
            child = card.layout().takeAt(0)
            if isinstance(child.widget(), QPushButton):
                assert child.widget().isEnabled() is False

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_task_card_update_task(
        self,
        setup_method,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Updated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_task = mocker.patch.object(TaskRepository, 'update_task')

        # Call the updateTask method
        self.card.updateTask()

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

    def test_task_card_update_task_db_error(self, setup_method, mocker: MockerFixture):
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
        self.card.updateTask()

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
    def test_task_card_remove_task(
        self,
        setup_method,
        mocker: MockerFixture,
        msgBoxResponse,
        expectedMethodCalls
    ):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_remove_task = mocker.patch.object(TaskRepository, 'remove_task')

        # Call the removeTask method
        self.card.removeTask()

        # Validate DB calls
        assert mock_remove_task.call_count == expectedMethodCalls

    def test_task_card_remove_task_db_error(self, setup_method, mocker: MockerFixture):
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
        self.card.removeTask()

        # Validate DB calls
        assert mock_remove_task.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_task_card_restore_task(
        self,
        setup_method,
        mocker: MockerFixture,
        msgBoxResponse,
        expectedMethodCalls
    ):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

        # Call the removeTask method
        self.card.restoreTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == expectedMethodCalls

    def test_task_card_restore_task_db_error(self, setup_method, mocker: MockerFixture):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_update_task_status = mocker.patch.object(
            TaskRepository,
            'update_task_status',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeTask method
        self.card.restoreTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "status_db,worker_task_id,status_worker",
            [
                ('pending_approval', '', ''),
                ('on_hold', '', ''),
                ('in_progress', 'abc', 'PENDING'),
                ('in_progress', 'abc', 'PROGRESS'),
                ('in_progress', 'abc', 'FAILURE'),
                ('finished', 'def', 'SUCCESS'),
                ('rejected', '', ''),
                ('cancelled', '', ''),
                ('cancelled', 'xyz', 'FAILURE')
            ]
        )
    def test_task_card_set_task_progress(
        self,
        qtbot: QtBot,
        mocker: MockerFixture,
        status_db,
        worker_task_id,
        status_worker
    ):
        # Mock task status
        self.task.status = status_db

        # Mock Celery task metadata
        task_info: Union[str, dict[str, int]] = ''
        if status_worker == 'FAILURE':
            task_info = 'Mocked error message'
        if status_worker == 'PROGRESS':
            task_info = {
                'sent_lines': 15,
                'processed_lines': 10,
                'total_lines': 20
            }
        task_metadata = {
            'status': status_worker,
            'result': task_info
        }

        # Mock Redis methods
        mocker.patch(
            'components.cards.TaskCard.get_value_from_id',
            return_value=worker_task_id
        )

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
        card = TaskCard(self.task, False)
        qtbot.addWidget(card)

        # Assertions
        expected_text = f'Tarea 1: Example task\nEstado: {status_db}'

        if status_worker == 'FAILURE':
            expected_text = (
                'Tarea 1: Example task\n'
                f'Estado: {status_db} (FAILED)\n'
                'Error: Mocked error message'
            )

        expected_sent = expected_processed = 0
        if status_worker == 'PROGRESS':
            expected_sent = 15
            expected_processed = 10

        assert card.label_description.text() == expected_text
        assert card.task_progress.sent_progress.value() == expected_sent
        assert card.task_progress.process_progress.value() == expected_processed
        assert mock_query_task.call_count == (1 if worker_task_id else 0)
        assert mock_query_task_info.call_count == (2 if worker_task_id else 0)

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_task_card_cancel_task(
        self,
        setup_method,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock TaskCancelDialog methods
        mock_input = 'A valid cancellation reason'
        mocker.patch.object(TaskCancelDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskCancelDialog, 'getInput', return_value=mock_input)

        # Mock DB method
        mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

        # Call the removeTask method
        self.card.cancelTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == expected_updated

    def test_task_card_cancel_task_db_error(self, setup_method, mocker: MockerFixture):
        # Mock TaskCancelDialog methods
        mock_input = 'A valid cancellation reason'
        mocker.patch.object(TaskCancelDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(TaskCancelDialog, 'getInput', return_value=mock_input)

        # Mock DB method
        mock_update_task_status = mocker.patch.object(
            TaskRepository,
            'update_task_status',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the removeTask method
        self.card.cancelTask()

        # Validate DB calls
        assert mock_update_task_status.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_task_card_repeat_task(
        self,
        setup_method,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Repeated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_create_task = mocker.patch.object(TaskRepository, 'create_task')

        # Call the updateTask method
        self.card.repeatTask()

        # Validate DB calls
        assert mock_create_task.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_task_params = {
                'user_id': 1,
                'file_id': 2,
                'tool_id': 3,
                'material_id': 4,
                'name': 'Repeated task',
                'note': 'Just a simple description'
            }
            mock_create_task.assert_called_with(*update_task_params.values())

    def test_task_card_repeat_task_db_error(self, setup_method, mocker: MockerFixture):
        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Repeated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_create_task = mocker.patch.object(
            TaskRepository,
            'create_task',
            side_effect=Exception('mocked error')
        )

        # Mock QMessageBox methods
        mock_popup = mocker.patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok)

        # Call the updateTask method
        self.card.repeatTask()

        # Validate DB calls
        assert mock_create_task.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxRun",
            [
                QMessageBox.Yes,
                QMessageBox.Cancel
            ]
        )
    @pytest.mark.parametrize("task_in_progress", [True, False])
    @pytest.mark.parametrize("device_enabled", [False, True])
    def test_task_card_run_task(
        self,
        setup_method,
        mocker,
        msgBoxRun,
        task_in_progress,
        device_enabled
    ):
        # Mock message box methods
        mocker.patch.object(
            QMessageBox,
            'exec',
            return_value=msgBoxRun
        )
        mock_info_popup = mocker.patch.object(
            QMessageBox,
            'information',
            return_value=QMessageBox.Ok
        )
        mock_error_popup = mocker.patch.object(
            QMessageBox,
            'critical',
            return_value=QMessageBox.Ok
        )
        # Mock worker monitor methods
        mocker.patch.object(CncWorkerMonitor, 'is_device_enabled', return_value=device_enabled)
        mocker.patch.object(CncWorkerMonitor, 'is_worker_running', return_value=task_in_progress)

        # Mock task manager methods
        mock_add_task_in_queue = mocker.patch('components.cards.TaskCard.send_task_to_worker')

        # Call the approveTask method
        self.card.runTask()

        # Validate call to tasks manager
        accepted_run = (msgBoxRun == QMessageBox.Yes)
        expected_run = not task_in_progress and accepted_run and device_enabled
        assert mock_add_task_in_queue.call_count == (1 if expected_run else 0)
        assert self.window.startWorkerMonitor.call_count == (1 if expected_run else 0)
        assert mock_info_popup.call_count == (1 if expected_run else 0)
        expected_error = (task_in_progress or not device_enabled) and accepted_run
        assert mock_error_popup.call_count == (1 if expected_error else 0)
