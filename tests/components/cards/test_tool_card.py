import pytest
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from components.cards.ToolCard import ToolCard
from components.dialogs.ToolDataDialog import ToolDataDialog
from database.models.tool import Tool
from views.InventoryView import InventoryView

class TestToolCard:
    tool = Tool(name='Example tool', description='Just a tool')

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(InventoryView, 'refreshLayout')

        self.parent = InventoryView()
        self.tool.id = 1
        self.card = ToolCard(self.tool, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_tool_card_init(self, qtbot):
        assert self.card.tool == self.tool
        assert self.card.layout() is not None

    def test_tool_card_update_tool(self, qtbot, mocker):
        # Mock ToolDataDialog methods
        mock_input = 'Updated tool', 'Updated description'
        mocker.patch.object(ToolDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(ToolDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_tool = mocker.patch('components.cards.ToolCard.updateTool')

        # Call the updateTool method
        self.card.updateTool()

        # Validate DB calls
        mock_update_tool.call_count == 1
        update_tool_params = {
            'id': 1,
            'name': 'Updated tool',
            'description': 'Updated description'
        }
        mock_update_tool.assert_called_with(*update_tool_params.values())

    def test_tool_card_remove_tool(self, qtbot, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_tool = mocker.patch('components.cards.ToolCard.removeTool')

        # Call the removeTool method
        self.card.removeTool()

        # Validate DB calls
        mock_remove_tool.call_count == 1
