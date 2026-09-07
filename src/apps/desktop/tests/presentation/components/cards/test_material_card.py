import pytest
from core.domain.entities import Material
from manager.adapters.desktop.presentation.components.cards.MaterialCard import MaterialCard
from manager.adapters.desktop.presentation.components.dialogs.MaterialDataDialog import (
    MaterialDataDialog,
)
from PyQt5.QtWidgets import QDialog, QMessageBox
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestMaterialCard:
    material = Material(name="Example material", description="Just a material")

    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mock_view):
        self.material.id = 1
        self.parent = mock_view
        self.card = MaterialCard(self.material, parent=self.parent)
        qtbot.addWidget(self.card)

    def test_material_card_init(self):
        assert self.card.material == self.material
        assert self.card.layout is not None

    @pytest.mark.parametrize(
        "dialogResponse,expected_emitted", [(QDialog.Accepted, True), (QDialog.Rejected, False)]
    )
    def test_material_card_update_material(
        self, mocker: MockerFixture, dialogResponse, expected_emitted
    ):
        mock_input = "Updated material", "Updated description"
        mocker.patch.object(MaterialDataDialog, "exec", return_value=dialogResponse)
        mocker.patch.object(MaterialDataDialog, "getInputs", return_value=mock_input)

        handler = mocker.Mock()
        self.card.update_requested.connect(handler)

        self.card.updateMaterial()

        if expected_emitted:
            handler.assert_called_once_with(
                self.material, "Updated material", "Updated description"
            )
        else:
            handler.assert_not_called()

    @pytest.mark.parametrize(
        "msgBoxResponse,expected_emitted", [(QMessageBox.Yes, True), (QMessageBox.Cancel, False)]
    )
    def test_material_card_remove_material(
        self, mocker: MockerFixture, msgBoxResponse, expected_emitted
    ):
        mocker.patch.object(QMessageBox, "exec", return_value=msgBoxResponse)

        handler = mocker.Mock()
        self.card.remove_requested.connect(handler)

        self.card.removeMaterial()

        if expected_emitted:
            handler.assert_called_once_with(self.material)
        else:
            handler.assert_not_called()
