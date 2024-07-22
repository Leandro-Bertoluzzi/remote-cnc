from components.cards.MaterialCard import MaterialCard
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from core.database.models import Material
from core.database.repositories.materialRepository import MaterialRepository
from PyQt5.QtWidgets import QDialog, QMessageBox
import pytest
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestMaterialCard:
    material = Material(name='Example material', description='Just a material')

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_view):
        # Update material
        self.material.id = 1

        # Instantiate card
        self.parent = mock_view
        self.card = MaterialCard(self.material, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_material_card_init(self):
        assert self.card.material == self.material
        assert self.card.layout is not None

    @pytest.mark.parametrize(
            "dialogResponse,expected_updated",
            [
                (QDialog.Accepted, True),
                (QDialog.Rejected, False)
            ]
        )
    def test_material_card_update_material(
        self,
        mocker: MockerFixture,
        dialogResponse,
        expected_updated
    ):
        # Mock MaterialDataDialog methods
        mock_input = 'Updated material', 'Updated description'
        mocker.patch.object(MaterialDataDialog, 'exec', return_value=dialogResponse)
        mocker.patch.object(MaterialDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_material = mocker.patch.object(MaterialRepository, 'update_material')

        # Call the updateMaterial method
        self.card.updateMaterial()

        # Validate DB calls
        assert mock_update_material.call_count == (1 if expected_updated else 0)

        if expected_updated:
            update_material_params = {
                'id': 1,
                'name': 'Updated material',
                'description': 'Updated description'
            }
            mock_update_material.assert_called_with(*update_material_params.values())

    def test_material_card_update_material_db_error(self, mocker: MockerFixture):
        # Mock MaterialDataDialog methods
        mock_input = 'Updated material', 'Updated description'
        mocker.patch.object(MaterialDataDialog, 'exec', return_value=QDialog.Accepted)
        mocker.patch.object(MaterialDataDialog, 'getInputs', return_value=mock_input)

        # Mock DB method
        mock_update_material = mocker.patch.object(
            MaterialRepository,
            'update_material',
            side_effect=Exception('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the updateMaterial method
        self.card.updateMaterial()

        # Assertions
        assert mock_update_material.call_count == 1
        assert mock_popup.call_count == 1

    @pytest.mark.parametrize(
            "msgBoxResponse,expectedMethodCalls",
            [
                (QMessageBox.Yes, 1),
                (QMessageBox.Cancel, 0)
            ]
        )
    def test_material_card_remove_material(
        self,
        mocker: MockerFixture,
        msgBoxResponse,
        expectedMethodCalls
    ):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=msgBoxResponse)

        # Mock DB method
        mock_remove_material = mocker.patch.object(MaterialRepository, 'remove_material')

        # Call the removeMaterial method
        self.card.removeMaterial()

        # Validate DB calls
        assert mock_remove_material.call_count == expectedMethodCalls

    def test_material_card_remove_material_db_error(self, mocker: MockerFixture):
        # Mock confirmation dialog methods
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Yes)

        # Mock DB method
        mock_remove_material = mocker.patch.object(
            MaterialRepository,
            'remove_material',
            side_effect=Exception('mocked error')
        )

        # Mock parent methods
        mock_popup = mocker.patch.object(self.parent, 'showError')

        # Call the removeMaterial method
        self.card.removeMaterial()

        # Validate DB calls
        assert mock_remove_material.call_count == 1
        assert mock_popup.call_count == 1
