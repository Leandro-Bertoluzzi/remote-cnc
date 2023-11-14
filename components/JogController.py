from containers.ButtonGrid import ButtonGrid
from core.grbl.grblController import GrblController, JOG_DISTANCE_ABSOLUTE, JOG_DISTANCE_INCREMENTAL, JOG_UNIT_INCHES, JOG_UNIT_MILIMETERS
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QButtonGroup, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QRadioButton, QVBoxLayout, QWidget

class JogController(QWidget):
    def __init__(self, grbl_controller: GrblController, parent=None):
        super(JogController, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Attributes definition
        self.grbl_controller = grbl_controller

        # State management
        self.step_x = 0.00
        self.step_y = 0.00
        self.step_z = 0.00
        self.feedrate = 0.00
        self.units = 'mm'

        # Widget structure and components definition

        joystick = ButtonGrid(
            [
                (' ↖ ', self.make_incremental_move(-1, 1, 0)),
                (' ↑ ', self.make_incremental_move(0, 1, 0)),
                (' ↗ ', self.make_incremental_move(1, 1, 0)),
                (' ← ', self.make_incremental_move(-1, 0, 0)),
                ('   ', self.make_incremental_move(0, 0, 0)),
                (' → ', self.make_incremental_move(1, 0, 0)),
                (' ↙ ', self.make_incremental_move(-1, -1, 0)),
                (' ↓ ', self.make_incremental_move(0, -1, 0)),
                (' ↘ ', self.make_incremental_move(1, -1, 0)),
            ],
            width=3,
            parent=self
        )
        layout.addWidget(joystick)

        self.form_layout = QFormLayout()

        label_x = QLabel('Paso en X:')
        self.input_x = QDoubleSpinBox()
        self.input_x.setDecimals(2)
        self.input_x.setRange(0, 10)
        self.input_x.setSingleStep(0.05)
        self.input_x.valueChanged.connect(self.set_step_x)
        self.form_layout.addRow(label_x, self.input_x)

        label_y = QLabel('Paso en Y:')
        self.input_y = QDoubleSpinBox()
        self.input_y.setDecimals(2)
        self.input_y.setRange(0, 10)
        self.input_y.setSingleStep(0.05)
        self.input_y.valueChanged.connect(self.set_step_y)
        self.form_layout.addRow(label_y, self.input_y)

        label_z = QLabel('Paso en Z:')
        self.input_z = QDoubleSpinBox()
        self.input_z.setDecimals(2)
        self.input_z.setRange(0, 10)
        self.input_z.setSingleStep(0.05)
        self.input_z.valueChanged.connect(self.set_step_z)
        self.form_layout.addRow(label_z, self.input_z)

        label_feedrate = QLabel('Velocidad de avance:')
        self.input_feedrate = QDoubleSpinBox()
        self.input_feedrate.setDecimals(2)
        # TO DO -> Actualizar feedrate según estado del dispositivo
        # TO DO -> Actualizar max y min feedrate según la configuración de GRBL
        # $110=800.000 (x max rate, mm/min)
        # $111=800.000 (y max rate, mm/min)
        # $112=350.000 (z max rate, mm/min)
        self.input_feedrate.setRange(0, 1000)
        self.input_feedrate.setSingleStep(25)
        self.input_feedrate.valueChanged.connect(self.set_feedrate)
        self.form_layout.addRow(label_feedrate, self.input_feedrate)

        label_units = QLabel('Unidades:')
        radio_mm = QRadioButton('Milímetros')
        radio_in = QRadioButton('Pulgadas')
        self.input_units = QHBoxLayout()
        self.input_units.addWidget(radio_mm)
        self.input_units.addWidget(radio_in)
        self.form_layout.addRow(label_units, self.input_units)
        self.control_units = QButtonGroup()
        self.control_units.addButton(radio_mm, 1)
        self.control_units.addButton(radio_in, 2)
        self.control_units.buttonClicked.connect(self.set_units)
        radio_mm.click()

        layout.addLayout(self.form_layout)

    def set_step_x(self, value):
        self.step_x = round(value, 2)

    def set_step_y(self, value):
        self.step_y = round(value, 2)

    def set_step_z(self, value):
        self.step_z = round(value, 2)

    def set_feedrate(self, value):
        self.feedrate = float(value)

    def set_units(self, button):
        selected_id = self.control_units.id(button)

        if selected_id == 1:
            self.units = 'mm'
        if selected_id == 2:
            self.units = 'in'

        self.input_x.setSuffix(' ' + self.units)
        self.input_y.setSuffix(' ' + self.units)
        self.input_z.setSuffix(' ' + self.units)
        self.input_feedrate.setSuffix(' ' + self.units + '/min')

    def make_incremental_move(self, x, y, z):
        def send_jog_incremental_move():
            move_x = x * self.step_x
            move_y = y * self.step_y
            move_z = z * self.step_z
            units = JOG_UNIT_MILIMETERS if self.units == 'mm' else JOG_UNIT_INCHES

            try:
                response = self.grbl_controller.jog(move_x, move_y, move_z, self.feedrate, units=units, distance_mode=JOG_DISTANCE_INCREMENTAL)
            except Exception as error:
                # TO DO: Show dialog with error message
                pass
        return send_jog_incremental_move
