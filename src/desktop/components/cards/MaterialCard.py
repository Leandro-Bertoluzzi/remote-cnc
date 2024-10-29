from desktop.components.cards.Card import Card
from desktop.components.dialogs.MaterialDataDialog import MaterialDataDialog
from database.base import SessionLocal
from database.models import Material
from database.repositories.materialRepository import MaterialRepository
from desktop.helpers.utils import needs_confirmation


class MaterialCard(Card):
    def __init__(self, material: Material, parent=None):
        super(MaterialCard, self).__init__(parent)

        self.material = material
        self.setup_ui()

    def setup_ui(self):
        description = f'Material {self.material.id}: {self.material.name}'
        self.setDescription(description)

        self.addButton("Editar", self.updateMaterial)
        self.addButton("Borrar", self.removeMaterial)

    def updateMaterial(self):
        materialDialog = MaterialDataDialog(materialInfo=self.material)
        if not materialDialog.exec():
            return

        name, description = materialDialog.getInputs()
        try:
            db_session = SessionLocal()
            repository = MaterialRepository(db_session)
            repository.update_material(self.material.id, name, description)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.getView().refreshLayout()

    @needs_confirmation('¿Realmente desea eliminar el material?', 'Eliminar material')
    def removeMaterial(self):
        try:
            db_session = SessionLocal()
            repository = MaterialRepository(db_session)
            repository.remove_material(self.material.id)
        except Exception as error:
            self.showError(
                'Error de base de datos',
                str(error)
            )
            return
        self.getView().refreshLayout()
