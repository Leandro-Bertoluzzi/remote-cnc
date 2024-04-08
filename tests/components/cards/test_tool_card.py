import pytest
from PyQt5.QtWidgets import QDialog, QMessageBox
from components.cards.ToolCard import ToolCard
from components.dialogs.ToolDataDialog import ToolDataDialog
from core.database.models import Tool
from core.database.repositories.toolRepository import ToolRepository
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestToolCard:
    tool = Tool(name='Example tool', description='Just a tool')

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_view):
        # Update tool
        self.tool.id = 1

        # Instantiate card
        self.parent = mock_view
        self.card = ToolCard(self.tool, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_tool_card_init(self):
        assert self.card.tool == self.tool
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_tool_card_update_tool(
        self,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock ToolDataDialog methods
        mock_input = 'Updated tool', 'Updated description'
        mocker.patch.object(ToolDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(ToolDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_tool = mocker.patch.object(ToolRepository, 'update_tool')

        # Call the updateTool method
        self.card.updateTool()

        # Validate DB calls
        assert mock_update_tool.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_tool_params = {
                'id': 1,
                'name': 'Updated tool',
                'description': 'Updated description'
            }
            mock_update_tool.assert_called_with(*update_tool_params.values())

    def test_tool_card_update_tool_db_error(self, mocker: MockerFixture):
        # Mock ToolDataDialog methods
        mock_input = 'Updated tool', 'Updated description'
        mocker.patch.object(ToolDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(ToolDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_tool = mocker.patch.object(
            ToolRepository,
            'update_tool',
            side_effect=Exception('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the updateTool method
        self.card.updateTool()

        # Validate DB calls
        assert mock_update_tool.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_tool_card_remove_tool(
        self,
        mocker: MockerFixture,
        msgBoxResponse,
        expectedMethodCalls
    ):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_remove_tool = mocker.patch.object(ToolRepository, 'remove_tool')

        # Call the removeTool method
        self.card.removeTool()

        # Validate DB calls
        assert mock_remove_tool.call_count == expectedMethodCalls

    def test_tool_card_remove_tool_db_error(self, mocker: MockerFixture):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_tool = mocker.patch.object(
            ToolRepository,
            'remove_tool',
            side_effect=Exception('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the removeTool method
        self.card.removeTool()

        # Validate DB calls
        assert mock_remove_tool.call_count == 1
        assert mock_popup.call_count == 1
