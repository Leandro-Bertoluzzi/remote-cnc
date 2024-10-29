import pytest
from desktop.components.dialogs.ToolDataDialog import ToolDataDialog
from database.models import Tool


class TestToolDataDialog:
    toolInfo = Tool(name='Example tool', description='Just a tool')

    def test_tool_data_dialog_init(self, qtbot):
        dialog = ToolDataDialog()
        qtbot.addWidget(dialog)

        assert dialog.layout() is not None

    @pytest.mark.parametrize("tool_info", [None, toolInfo])
    def test_tool_data_dialog_init_widgets(self, qtbot, tool_info):
        dialog = ToolDataDialog(toolInfo=tool_info)
        qtbot.addWidget(dialog)

        expectedName = self.toolInfo.name if tool_info else ''
        expectedDescription = self.toolInfo.description if tool_info else ''
        expectedWindowTitle = 'Actualizar herramienta' if tool_info else 'Agregar herramienta'

        assert dialog.name.text() == expectedName
        assert dialog.description.toPlainText() == expectedDescription
        assert dialog.windowTitle() == expectedWindowTitle

    def test_tool_data_dialog_get_inputs(self, qtbot):
        dialog = ToolDataDialog(toolInfo=self.toolInfo)
        qtbot.addWidget(dialog)

        # Interaction with widget
        dialog.name.setText('Updated tool name')
        dialog.description.setPlainText('Updated tool description')

        assert dialog.getInputs() == ('Updated tool name', 'Updated tool description')
