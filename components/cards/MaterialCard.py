from PyQt5.QtWidgets import QPushButton, QMessageBox
from components.cards.Card import Card
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from core.database.base import Session as SessionLocal
from core.database.repositories.materialRepository import MaterialRepository


class MaterialCard(Card):
    def __init__(self, material, parent=None):
        super(MaterialCard, self).__init__(parent)

        self.material = material

        description = f'Material {material.id}: {material.name}'
        editMaterialBtn = QPushButton("Editar")
        editMaterialBtn.clicked.connect(self.updateMaterial)
        removeMaterialBtn = QPushButton("Borrar")
        removeMaterialBtn.clicked.connect(self.removeMaterial)

        self.setDescription(description)
        self.addButton(editMaterialBtn)
        self.addButton(removeMaterialBtn)

    def updateMaterial(self):
        materialDialog = MaterialDataDialog(materialInfo=self.material)
        if materialDialog.exec():
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
            self.parent().refreshLayout()

    def removeMaterial(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar el material?')
        confirmation.setWindowTitle('Eliminar material')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
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
            self.parent().refreshLayout()
