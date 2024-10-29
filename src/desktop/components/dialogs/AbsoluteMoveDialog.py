from desktop.containers.WidgetsHList import WidgetsHList
from utilities.grbl.grblController import GrblController
from utilities.grbl.grblUtils import JOG_DISTANCE_ABSOLUTE
from desktop.mixins.JogController import JogController
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt5.QtCore import Qt


class AbsoluteMoveDialog(QDialog, JogController):
    def __init__(self, grbl_controller: GrblController, parent=None):
        super(AbsoluteMoveDialog, self).__init__(parent)
        self.set_controller(grbl_controller)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        layout.addWidget(QLabel('Mover a posición (absoluta): '))
        self.abs_controls = self.create_abs_controls()
        layout.addWidget(self.abs_controls)

        label_feedrate = QLabel('Avance:')
        # TO DO -> Actualizar feedrate según estado del dispositivo
        # TO DO -> Actualizar max y min feedrate según la configuración de GRBL
        # $110=800.000 (x max rate, mm/min)
        # $111=800.000 (y max rate, mm/min)
        # $112=350.000 (z max rate, mm/min)
        self.input_feedrate = self.create_double_spinbox(0, 1000, 25, 2)
        row_feedrate = WidgetsHList([label_feedrate, self.input_feedrate])
        layout.addWidget(row_feedrate)

        _, layout_units = self.create_units_radio_buttons()
        layout.addLayout(layout_units)

        # We ensure the correct units are shown in the widgets
        self.control_units.buttons()[0].click()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

        self.setWindowTitle('Mover a')

    def getInputs(self):
        return (
            self.input_x.value(),
            self.input_y.value(),
            self.input_z.value(),
            self.input_feedrate.value()
        )

    # UI methods

    def create_abs_controls(self):
        # TO DO -> Actualizar limites según la configuración de soft-limits de GRBL
        # (si es que están configurados)
        # $20=0 	Soft limits, boolean
        # $130=200.000 	X Max travel, mm
        # $131=200.000 	Y Max travel, mm
        # $132=200.000 	Z Max travel, mm
        self.input_x = self.create_double_spinbox(0, 200, 0.25, 2)
        self.input_y = self.create_double_spinbox(0, 200, 0.25, 2)
        self.input_z = self.create_double_spinbox(0, 200, 0.25, 2)
        return WidgetsHList([
            QLabel('X: '), self.input_x,
            QLabel('Y: '), self.input_y,
            QLabel('Z: '), self.input_z
        ])

    def set_units(self, button):
        selected_id = self.control_units.id(button)
        self.units = selected_id

        unit_info = self.UNIT_MAPPING[selected_id]

        for input in [
            self.input_x,
            self.input_y,
            self.input_z,
        ]:
            input.setSuffix(unit_info['suffix'])

        self.input_feedrate.setSuffix(unit_info['suffix'] + '/min')

    # GRBL controller interaction

    def make_absolute_move(self):
        x = round(self.input_x.value(), 2)
        y = round(self.input_y.value(), 2)
        z = round(self.input_z.value(), 2)
        feedrate = round(self.input_feedrate.value(), 2)

        self.send_jog_command(x, y, z, feedrate, JOG_DISTANCE_ABSOLUTE)
