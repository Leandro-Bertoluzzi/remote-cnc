import pytest
from PyQt5.QtWidgets import QDialogButtonBox

from MainWindow import MainWindow
from components.MenuButton import MenuButton
from components.cards.ToolCard import ToolCard
from components.cards.MaterialCard import MaterialCard
from components.dialogs.ToolDataDialog import ToolDataDialog
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from views.InventoryView import InventoryView
from database.models.tool import Tool
from database.models.material import Material

class TestInventoryView:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        tool_1 = Tool(name='Example tool 1', description='It is the first tool')
        tool_2 = Tool(name='Example tool 2', description='It is the second tool')
        tool_3 = Tool(name='Example tool 3', description='It is the third tool')
        self.tools_list = [tool_1, tool_2, tool_3]

        # Patch the getAllTools method with the mock function
        self.mock_get_all_tools = mocker.patch('views.InventoryView.getAllTools', return_value=self.tools_list)

        material_1 = Material(name='Example material 1', description='It is the first material')
        material_2 = Material(name='Example material 2', description='It is the second material')
        material_3 = Material(name='Example material 3', description='It is the third material')
        self.materials_list = [material_1, material_2, material_3]

        # Patch the getAllMaterials method with the mock function
        self.mock_get_all_materials = mocker.patch('views.InventoryView.getAllMaterials', return_value=self.materials_list)

        # Create an instance of InventoryView
        self.parent = MainWindow()
        self.inventory_view = InventoryView(parent=self.parent)
        qtbot.addWidget(self.inventory_view)

    def test_inventory_view_init(self, helpers):
        # Validate DB calls
        self.mock_get_all_tools.assert_called_once()
        self.mock_get_all_materials.assert_called_once()

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MenuButton) == 3
        assert helpers.count_widgets_with_type(self.inventory_view.layout, ToolCard) == 3
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MaterialCard) == 3

    def test_inventory_view_refresh_layout(self, helpers):
        # We remove a tool
        self.tools_list.pop()
        # We remove a material
        self.materials_list.pop()

        # Call the refreshLayout method
        self.inventory_view.refreshLayout()

        # Validate DB calls
        assert self.mock_get_all_tools.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MenuButton) == 3
        assert helpers.count_widgets_with_type(self.inventory_view.layout, ToolCard) == 2
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MaterialCard) == 2

    def test_inventory_view_create_tool(self, mocker, helpers):
        # Mock ToolDataDialog methods
        mock_inputs = 'Example tool 4', 'It is the fourth tool'
        mocker.patch.object(ToolDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(ToolDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method
        def side_effect_create_tool(name, description):
            tool_4 = Tool(name='Example tool 4', description='It is the fourth tool')
            self.tools_list.append(tool_4)
            return

        mock_create_tool = mocker.patch('views.InventoryView.createTool', side_effect=side_effect_create_tool)

        # Call the createTool method
        self.inventory_view.createTool()

        # Validate DB calls
        assert mock_create_tool.call_count == 1
        assert self.mock_get_all_tools.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MenuButton) == 3
        assert helpers.count_widgets_with_type(self.inventory_view.layout, ToolCard) == 4
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MaterialCard) == 3

    def test_inventory_view_create_material(self, mocker, helpers):
        # Mock MaterialDataDialog methods
        mock_inputs = 'Example material 4', 'It is the fourth material'
        mocker.patch.object(MaterialDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(MaterialDataDialog, 'getInputs', return_value=mock_inputs)

        # Mock DB method
        def side_effect_create_material(name, description):
            material_4 = Material(name='Example material 4', description='It is the fourth material')
            self.materials_list.append(material_4)
            return

        mock_create_material = mocker.patch('views.InventoryView.createMaterial', side_effect=side_effect_create_material)

        # Call the createMaterial method
        self.inventory_view.createMaterial()

        # Validate DB calls
        assert mock_create_material.call_count == 1
        assert self.mock_get_all_materials.call_count == 2

        # Validate amount of each type of widget
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MenuButton) == 3
        assert helpers.count_widgets_with_type(self.inventory_view.layout, ToolCard) == 3
        assert helpers.count_widgets_with_type(self.inventory_view.layout, MaterialCard) == 4
