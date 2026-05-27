from core.domain.entities import Material
from desktop.components.cards.Card import Card
from desktop.components.dialogs.MaterialDataDialog import MaterialDataDialog
from desktop.helpers.utils import needs_confirmation


class MaterialCard(Card):
    def __init__(self, material: Material, parent=None):
        super(MaterialCard, self).__init__(parent)

        self.material = material
        self.setup_ui()

    def setup_ui(self):
        description = f"Material {self.material.id}: {self.material.name}"
        self.setDescription(description)

        self.addButton("Editar", self.updateMaterial)
        self.addButton("Borrar", self.removeMaterial)

    def updateMaterial(self):
        materialDialog = MaterialDataDialog(materialInfo=self.material)
        if not materialDialog.exec():
            return

        if self.material.id is None:
            raise ValueError("Material ID is required")

        name, description = materialDialog.getInputs()
        try:
            self._context.material_service.update_material(self.material.id, name, description)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.getView().refreshLayout()

    @needs_confirmation("¿Realmente desea eliminar el material?", "Eliminar material")
    def removeMaterial(self):
        if self.material.id is None:
            raise ValueError("Material ID is required")

        try:
            self._context.material_service.remove_material(self.material.id)
        except Exception as error:
            self.showError("Error de base de datos", str(error))
            return
        self.getView().refreshLayout()
