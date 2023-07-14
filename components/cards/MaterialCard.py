from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from utils.files import getFileNameInFolder
from components.dialogs.MaterialDataDialog import MaterialDataDialog
from database.repositories.materialRepository import updateMaterial, removeMaterial

class MaterialCard(QWidget):
    def __init__(self, material, parent=None):
        super(MaterialCard, self).__init__(parent)

        self.material = material

        materialDescription = QLabel(f'Tarea {material.id}: {material.name}')
        editMaterialBtn = QPushButton("Editar")
        editMaterialBtn.clicked.connect(self.updateMaterial)
        removeMaterialBtn = QPushButton("Borrar")
        removeMaterialBtn.clicked.connect(self.removeMaterial)

        layout = QHBoxLayout()
        layout.addWidget(materialDescription)
        layout.addWidget(editMaterialBtn)
        layout.addWidget(removeMaterialBtn)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        stylesheet = getFileNameInFolder(__file__, "Card.qss")
        with open(stylesheet,"r") as styles:
            self.setStyleSheet(styles.read())

    def updateMaterial(self):
        materialDialog = MaterialDataDialog(materialInfo=self.material)
        if materialDialog.exec():
            name, description = materialDialog.getInputs()
            updateMaterial(self.material.id, name, description)
            self.parent().refreshLayout()

    def removeMaterial(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setText('¿Realmente desea eliminar el material?')
        confirmation.setWindowTitle('Eliminar material')
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        if confirmation.exec() == QMessageBox.Yes:
            removeMaterial(self.material.id)
            self.parent().refreshLayout()
