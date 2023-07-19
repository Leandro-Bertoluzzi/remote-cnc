import pytest
from PyQt5.QtWidgets import QDialogButtonBox, QMessageBox
from components.cards.MaterialCard import MaterialCard
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from database.models.material import Material
from views.InventoryView import InventoryView

class TestMaterialCard:
    material = Material(name='Example material', description='Just a material')

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        mocker.patch.object(InventoryView, 'refreshLayout')

        self.parent = InventoryView()
        self.material.id = 1
        self.card = MaterialCard(self.material, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_material_card_init(self, qtbot):
        assert self.card.material == self.material
        assert self.card.layout() is not None

    def test_material_card_update_material(self, qtbot, mocker):
        # Mock MaterialDataDialog methods
        mock_input = 'Updated material', 'Updated description'
        mocker.patch.object(MaterialDataDialog, 'exec', return_value=QDialogButtonBox.Save)
        mocker.patch.object(MaterialDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_material = mocker.patch('components.cards.MaterialCard.updateMaterial')

        # Call the updateMaterial method
        self.card.updateMaterial()

        # Validate DB calls
        mock_update_material.call_count == 1
        update_material_params = {
            'id': 1,
            'name': 'Updated material',
            'description': 'Updated description'
        }
        mock_update_material.assert_called_with(*update_material_params.values())

    def test_material_card_remove_material(self, qtbot, mocker):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_material = mocker.patch('components.cards.MaterialCard.removeMaterial')

        # Call the removeMaterial method
        self.card.removeMaterial()

        # Validate DB calls
        mock_remove_material.call_count == 1
