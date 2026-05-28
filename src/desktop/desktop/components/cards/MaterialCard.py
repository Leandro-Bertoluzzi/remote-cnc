from core.domain.entities import Material
from desktop.components.cards.Card import Card
from desktop.components.dialogs.MaterialDataDialog import MaterialDataDialog
from desktop.helpers.utils import needs_confirmation
from PyQt5.QtCore import pyqtSignal


class MaterialCard(Card):
    """Presentation-only card for a Material entity."""

    # (material, name, description)
    update_requested = pyqtSignal(object, str, str)
    # (material,)
    remove_requested = pyqtSignal(object)

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

        name, description = materialDialog.getInputs()
        self.update_requested.emit(self.material, name, description)

    @needs_confirmation("¿Realmente desea eliminar el material?", "Eliminar material")
    def removeMaterial(self):
        self.remove_requested.emit(self.material)
