import pytest
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from core.database.models.material import Material


class TestMaterialDataDialog:
    materialInfo = Material(name='Example material', description='Just a material')

    def test_material_data_dialog_init(self, qtbot):
        dialog = MaterialDataDialog()
        qtbot.addWidget(dialog)

        assert dialog.layout() is not None

    @pytest.mark.parametrize("material_info", [None, materialInfo])
    def test_material_data_dialog_init_widgets(self, qtbot, material_info):
        dialog = MaterialDataDialog(materialInfo=material_info)
        qtbot.addWidget(dialog)

        expectedName = self.materialInfo.name if material_info else ''
        expectedDescription = self.materialInfo.description if material_info else ''
        expectedWindowTitle = 'Actualizar material' if material_info else 'Agregar material'

        assert dialog.name.text() == expectedName
        assert dialog.description.toPlainText() == expectedDescription
        assert dialog.windowTitle() == expectedWindowTitle

    def test_material_data_dialog_get_inputs(self, qtbot):
        dialog = MaterialDataDialog(materialInfo=self.materialInfo)
        qtbot.addWidget(dialog)

        # Interaction with widget
        dialog.name.setText('Updated material name')
        dialog.description.setPlainText('Updated material description')

        assert dialog.getInputs() == ('Updated material name', 'Updated material description')
