import pytest
from core.domain.entities import Material, Tool
from desktop.components.buttons.MenuButton import MenuButton
from desktop.components.cards.MaterialCard import MaterialCard
from desktop.components.cards.MsgCard import MsgCard
from desktop.components.cards.ToolCard import ToolCard
from desktop.components.ConnectionErrorWidget import ConnectionErrorWidget
from desktop.components.dialogs.MaterialDataDialog import MaterialDataDialog
from desktop.components.dialogs.ToolDataDialog import ToolDataDialog
from desktop.MainWindow import MainWindow
from desktop.views.InventoryView import InventoryView
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestInventoryView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_window: MainWindow):
        tool_1 = Tool(name="Example tool 1", description="It is the first tool")
        tool_2 = Tool(name="Example tool 2", description="It is the second tool")
        tool_3 = Tool(name="Example tool 3", description="It is the third tool")
        self.tools_list = [tool_1, tool_2, tool_3]

        material_1 = Material(name="Example material 1", description="It is the first material")
        material_2 = Material(name="Example material 2", description="It is the second material")
        material_3 = Material(name="Example material 3", description="It is the third material")
        self.materials_list = [material_1, material_2, material_3]

        # Configure context service mocks
        self.parent = mock_window
        self.mock_tool_service = mock_window._context.tool_service
        self.mock_material_service = mock_window._context.material_service
        self.mock_tool_service.get_all_tools.return_value = self.tools_list
        self.mock_material_service.get_all_materials.return_value = self.materials_list

        self.inventory_view = InventoryView(self.parent)
        qtbot.addWidget(self.inventory_view)

        # Reset call counts accumulated during view creation
        self.mock_tool_service.get_all_tools.reset_mock()
        self.mock_material_service.get_all_materials.reset_mock()

    def test_inventory_view_init(self, helpers):
        assert helpers.count_widgets(self.inventory_view.layout(), MenuButton) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), ToolCard) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), MaterialCard) == 3

    def test_inventory_view_init_with_no_inventory(self, helpers):
        self.mock_tool_service.get_all_tools.return_value = []
        self.mock_material_service.get_all_materials.return_value = []
        inventory_view = InventoryView(self.parent)

        assert helpers.count_widgets(inventory_view.layout(), MenuButton) == 3
        assert helpers.count_widgets(inventory_view.layout(), ToolCard) == 0
        assert helpers.count_widgets(inventory_view.layout(), MaterialCard) == 0
        assert helpers.count_widgets(inventory_view.layout(), MsgCard) == 2

    @pytest.mark.parametrize("tools_error,materials_error", [(False, True), (True, False)])
    def test_inventory_view_init_db_error(self, helpers, tools_error, materials_error):
        if tools_error:
            self.mock_tool_service.get_all_tools.side_effect = Exception("mocked-error")
            self.mock_tool_service.get_all_tools.return_value = None
        else:
            self.mock_tool_service.get_all_tools.return_value = self.tools_list
            self.mock_tool_service.get_all_tools.side_effect = None

        if materials_error:
            self.mock_material_service.get_all_materials.side_effect = Exception("mocked-error")
            self.mock_material_service.get_all_materials.return_value = None
        else:
            self.mock_material_service.get_all_materials.return_value = self.materials_list
            self.mock_material_service.get_all_materials.side_effect = None

        inventory_view = InventoryView(self.parent)

        assert helpers.count_widgets(inventory_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(inventory_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(inventory_view.layout(), ToolCard) == 0
        assert helpers.count_widgets(inventory_view.layout(), MaterialCard) == 0
        assert helpers.count_widgets(inventory_view.layout(), MsgCard) == 0

    def test_inventory_view_refresh_layout(self, helpers):
        self.tools_list.pop()
        self.materials_list.pop()

        self.inventory_view.refreshLayout()

        assert self.mock_tool_service.get_all_tools.call_count == 1

        assert helpers.count_widgets(self.inventory_view.layout(), MenuButton) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), ToolCard) == 2
        assert helpers.count_widgets(self.inventory_view.layout(), MaterialCard) == 2

    @pytest.mark.parametrize("tools_error,materials_error", [(False, True), (True, False)])
    def test_inventory_view_refresh_layout_db_error(self, helpers, tools_error, materials_error):
        if tools_error:
            self.mock_tool_service.get_all_tools.side_effect = Exception("mocked-error")
        else:
            self.mock_material_service.get_all_materials.side_effect = Exception("mocked-error")

        self.inventory_view.refreshLayout()

        assert self.mock_tool_service.get_all_tools.call_count == 1
        assert self.mock_material_service.get_all_materials.call_count == (0 if tools_error else 1)
        assert helpers.count_widgets(self.inventory_view.layout(), ConnectionErrorWidget) == 1
        assert helpers.count_widgets(self.inventory_view.layout(), MenuButton) == 0
        assert helpers.count_widgets(self.inventory_view.layout(), ToolCard) == 0
        assert helpers.count_widgets(self.inventory_view.layout(), MaterialCard) == 0

    def test_inventory_view_create_tool(self, mocker: MockerFixture, helpers):
        mock_inputs = "Example tool 4", "It is the fourth tool"
        mocker.patch.object(ToolDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(ToolDataDialog, "getInputs", return_value=mock_inputs)

        def side_effect_create_tool(name, description):
            tool_4 = Tool(name="Example tool 4", description="It is the fourth tool")
            self.tools_list.append(tool_4)

        self.mock_tool_service.create_tool.side_effect = side_effect_create_tool

        self.inventory_view.createTool()

        assert self.mock_tool_service.create_tool.call_count == 1
        assert self.mock_tool_service.get_all_tools.call_count == 1

        assert helpers.count_widgets(self.inventory_view.layout(), MenuButton) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), ToolCard) == 4
        assert helpers.count_widgets(self.inventory_view.layout(), MaterialCard) == 3

    def test_inventory_view_create_tool_db_error(self, mocker: MockerFixture, helpers):
        mock_inputs = "Example tool 4", "It is the fourth tool"
        mocker.patch.object(ToolDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(ToolDataDialog, "getInputs", return_value=mock_inputs)

        self.mock_tool_service.create_tool.side_effect = Exception("mocked-error")
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        self.inventory_view.createTool()

        assert self.mock_tool_service.create_tool.call_count == 1
        assert mock_popup.call_count == 1
        assert self.mock_tool_service.get_all_tools.call_count == 0

        assert helpers.count_widgets(self.inventory_view.layout(), MenuButton) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), ToolCard) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), MaterialCard) == 3

    def test_inventory_view_create_material(self, mocker: MockerFixture, helpers):
        mock_inputs = "Example material 4", "It is the fourth material"
        mocker.patch.object(MaterialDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(MaterialDataDialog, "getInputs", return_value=mock_inputs)

        def side_effect_create_material(name, description):
            material_4 = Material(
                name="Example material 4", description="It is the fourth material"
            )
            self.materials_list.append(material_4)

        self.mock_material_service.create_material.side_effect = side_effect_create_material

        self.inventory_view.createMaterial()

        assert self.mock_material_service.create_material.call_count == 1
        assert self.mock_material_service.get_all_materials.call_count == 1

        assert helpers.count_widgets(self.inventory_view.layout(), MenuButton) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), ToolCard) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), MaterialCard) == 4

    def test_inventory_view_create_material_db_error(self, mocker: MockerFixture, helpers):
        mock_inputs = "Example material 4", "It is the fourth material"
        mocker.patch.object(MaterialDataDialog, "exec", return_value=QDialogButtonBox.Save)
        mocker.patch.object(MaterialDataDialog, "getInputs", return_value=mock_inputs)

        self.mock_material_service.create_material.side_effect = Exception("mocked-error")
        mock_popup = mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)

        self.inventory_view.createMaterial()

        assert self.mock_material_service.create_material.call_count == 1
        assert mock_popup.call_count == 1
        assert self.mock_material_service.get_all_materials.call_count == 0

        assert helpers.count_widgets(self.inventory_view.layout(), MenuButton) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), ToolCard) == 3
        assert helpers.count_widgets(self.inventory_view.layout(), MaterialCard) == 3

    # Handler tests

    def test_inventory_view_on_tool_update_success(self):
        tool = self.tools_list[0]
        tool.id = 1
        self.inventory_view.on_tool_update(tool, "Updated tool", "Updated desc")
        self.mock_tool_service.update_tool.assert_called_once_with(
            1, "Updated tool", "Updated desc"
        )
        assert self.mock_tool_service.get_all_tools.call_count == 1

    def test_inventory_view_on_tool_update_error(self, mocker: MockerFixture):
        self.mock_tool_service.update_tool.side_effect = Exception("e")
        mock_error = mocker.patch.object(self.inventory_view, "showError")
        tool = self.tools_list[0]
        tool.id = 1
        self.inventory_view.on_tool_update(tool, "name", "desc")
        assert mock_error.call_count == 1
        assert self.mock_tool_service.get_all_tools.call_count == 0

    def test_inventory_view_on_tool_remove_success(self):
        tool = self.tools_list[0]
        tool.id = 1
        self.inventory_view.on_tool_remove(tool)
        self.mock_tool_service.remove_tool.assert_called_once_with(1)
        assert self.mock_tool_service.get_all_tools.call_count == 1

    def test_inventory_view_on_material_update_success(self):
        material = self.materials_list[0]
        material.id = 1
        self.inventory_view.on_material_update(material, "Updated material", "Updated desc")
        self.mock_material_service.update_material.assert_called_once_with(
            1, "Updated material", "Updated desc"
        )
        assert self.mock_material_service.get_all_materials.call_count == 1

    def test_inventory_view_on_material_remove_success(self):
        material = self.materials_list[0]
        material.id = 1
        self.inventory_view.on_material_remove(material)
        self.mock_material_service.remove_material.assert_called_once_with(1)
        assert self.mock_material_service.get_all_materials.call_count == 1
