import pytest
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from components.cards.TaskCard import TaskCard
from components.dialogs.TaskDataDialog import TaskDataDialog
from database.models.task import Task
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
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(TasksView, 'refreshLayout')

        # Patch the DB methods
        mocker.patch('views.TasksView.getAllFilesFromUser', return_value=[])
        mocker.patch('views.TasksView.getAllTools', return_value=[])
        mocker.patch('views.TasksView.getAllMaterials', return_value=[])

        self.parent = TasksView()
        self.task.id = 1
        self.card = TaskCard(self.task, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_task_card_init(self, qtbot):
        assert self.card.task == self.task
        assert self.card.layout() is not None

    def test_task_card_update_task(self, qtbot, mocker):
        # Mock TaskDataDialog methods
        mock_input = 2, 3, 4, 'Updated task', 'Just a simple description'
        mocker.patch.object(TaskDataDialog, '__init__', return_value=None)
        mocker.patch.object(TaskDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(TaskDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_task = mocker.patch('components.cards.TaskCard.updateTask')

        # Call the updateTask method
        self.card.updateTask()

        # Validate DB calls
        mock_update_task.call_count == 1
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

    def test_task_card_remove_task(self, qtbot, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_task = mocker.patch('components.cards.TaskCard.removeTask')

        # Call the removeTask method
        self.card.removeTask()

        # Validate DB calls
        mock_remove_task.call_count == 1
