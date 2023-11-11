import pytest
from components.dialogs.TaskDataDialog import TaskDataDialog
from core.database.models.file import File
from core.database.models.material import Material
from core.database.models.task import Task
from core.database.models.tool import Tool

class TestTaskDataDialog:
    taskInfo = Task(
        user_id=1,
        file_id=1,
        tool_id=1,
        material_id=1,
        name='Example task',
        note='Just a task'
    )

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot):
        # Mock DB data
        file = File(user_id=1, file_name='example_file.gcode', file_path='path/example_file.gcode')
        file.id = 1
        material = Material(name='Example material', description='Just a material')
        material.id = 1
        tool = Tool(name='Example tool', description='Just a tool')
        tool.id = 1

        # Mock objects related to the task
        self.taskInfo.file = file
        self.taskInfo.material = material
        self.taskInfo.tool = tool

        # Mock arrays from DB
        self.files = [{'id': item.id, 'name': item.file_name} for item in [file]]
        self.materials = [{'id': item.id, 'name': item.name} for item in [material]]
        self.tools = [{'id': item.id, 'name': item.name} for item in [tool]]

    def test_task_data_dialog_init(self, qtbot):
        # Instantiate the dialog
        dialog = TaskDataDialog(files=self.files, tools=self.tools, materials=self.materials)
        qtbot.addWidget(dialog)

        assert dialog.layout() is not None

    @pytest.mark.parametrize("task_info", [None, taskInfo])
    def test_task_data_dialog_init_widgets(self, qtbot, task_info):
        dialog = TaskDataDialog(
            files=self.files,
            tools=self.tools,
            materials=self.materials,
            taskInfo=task_info
        )
        qtbot.addWidget(dialog)

        expectedName = self.taskInfo.name if task_info is not None else ''
        expectedNote = self.taskInfo.note if task_info is not None else ''
        expectedWindowTitle = 'Actualizar tarea' if task_info is not None else 'Crear tarea'

        assert dialog.name.text() == expectedName
        assert dialog.note.toPlainText() == expectedNote
        assert dialog.file.currentText() == 'example_file.gcode'
        assert dialog.material.currentText() == 'Example material'
        assert dialog.tool.currentText() == 'Example tool'
        assert dialog.windowTitle() == expectedWindowTitle

    def test_task_data_dialog_get_inputs(self, qtbot):
        dialog = TaskDataDialog(
            files=self.files,
            tools=self.tools,
            materials=self.materials,
            taskInfo=self.taskInfo
        )
        qtbot.addWidget(dialog)

        # Interaction with widget
        dialog.name.setText('Updated task name')
        dialog.note.setPlainText('Updated task note')

        assert dialog.getInputs() == (1, 1, 1, 'Updated task name', 'Updated task note')
