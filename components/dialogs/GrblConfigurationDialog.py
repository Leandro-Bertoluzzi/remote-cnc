from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox, QTableWidget, \
    QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from core.grbl.types import GrblSettings


class GrblConfigurationDialog(QDialog):
    def __init__(self, device_settings: GrblSettings, parent=None):
        super(GrblConfigurationDialog, self).__init__(parent)

        # Variables
        self.modifiedSettings: dict[str, str] = {}

        # Table definition

        self.settings = QTableWidget(self)
        self.settings.setRowCount(len(device_settings))
        self.settings.setColumnCount(4)
        self.settings.setHorizontalHeaderLabels(
            [
                'value',
                'message',
                'units',
                'description'
            ]
        )
        self.settings.setVerticalHeaderLabels(device_settings.keys())

        header = self.settings.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        # Buttons

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        # Layout

        layout = QVBoxLayout(self)
        layout.addWidget(self.settings)
        layout.addWidget(buttonBox)

        # Draw the table
        index = 0
        for setting in device_settings.values():
            messageCell = QTableWidgetItem(setting['message'])
            messageCell.setFlags(Qt.ItemIsEnabled)
            unitsCell = QTableWidgetItem(setting['units'])
            unitsCell.setFlags(Qt.ItemIsEnabled)
            descriptionCell = QTableWidgetItem(setting['description'])
            descriptionCell.setFlags(Qt.ItemIsEnabled)

            self.settings.setItem(index, 0, QTableWidgetItem(setting['value']))
            self.settings.setItem(index, 1, messageCell)
            self.settings.setItem(index, 2, unitsCell)
            self.settings.setItem(index, 3, descriptionCell)

            index = index + 1

        self.settings.cellChanged.connect(self.updateModifiedItems)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.setWindowTitle('Configurar GRBL')

    def updateModifiedItems(self, row, column):
        parameter = self.settings.verticalHeaderItem(row).text()
        value = self.settings.item(row, 0).text()
        self.settings.item(row, 0).setBackground(QColor(19, 178, 45))
        self.modifiedSettings[parameter] = value

    def getModifiedInputs(self):
        return self.modifiedSettings
