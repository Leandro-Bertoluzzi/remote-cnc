from containers.ButtonGrid import ButtonGrid
from containers.WidgetsHList import WidgetsHList
from core.grbl.grblController import GrblController
from core.grbl.grblUtils import JOG_DISTANCE_ABSOLUTE, JOG_DISTANCE_INCREMENTAL, \
    JOG_UNIT_INCHES, JOG_UNIT_MILIMETERS
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QButtonGroup, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, \
    QLabel, QPushButton, QRadioButton, QSizePolicy, QVBoxLayout, QWidget


class JogController(QWidget):
    UNIT_MAPPING = {
        1: {'suffix': ' mm', 'distance_unit': JOG_UNIT_MILIMETERS},
        2: {'suffix': ' in', 'distance_unit': JOG_UNIT_INCHES}
    }

    def __init__(
            self,
            grbl_controller: GrblController,
            parent=None
    ):
        super(JogController, self).__init__(parent)

        # Attributes definition
        self.grbl_controller = grbl_controller
        self.units = 1  # Default to millimeters
        self.setup_ui()

    # UI methods

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Widget structure and components definition

        joystick = self.create_joystick()
        layout.addWidget(joystick)

        self.layout_config = QFormLayout()

        label_x = QLabel('Paso en X:')
        self.input_x = self.create_double_spinbox(0, 10, 0.05, 2)
        self.layout_config.addRow(label_x, self.input_x)

        label_y = QLabel('Paso en Y:')
        self.input_y = self.create_double_spinbox(0, 10, 0.05, 2)
        self.layout_config.addRow(label_y, self.input_y)

        label_z = QLabel('Paso en Z:')
        self.input_z = self.create_double_spinbox(0, 10, 0.05, 2)
        self.layout_config.addRow(label_z, self.input_z)

        label_feedrate = QLabel('Velocidad de avance:')
        # TO DO -> Actualizar feedrate según estado del dispositivo
        # TO DO -> Actualizar max y min feedrate según la configuración de GRBL
        # $110=800.000 (x max rate, mm/min)
        # $111=800.000 (y max rate, mm/min)
        # $112=350.000 (z max rate, mm/min)
        self.input_feedrate = self.create_double_spinbox(0, 1000, 25, 2)
        self.layout_config.addRow(label_feedrate, self.input_feedrate)

        self.create_units_radio_buttons()

        layout.addLayout(self.layout_config)

        separator = self.create_separator()
        layout.addWidget(separator)

        layout.addWidget(QLabel('Mover a posición (absoluta): '))
        self.abs_controls = self.create_abs_controls()
        layout.addWidget(self.abs_controls)

        layout.addWidget(btn_absolute_move := QPushButton('Mover'))
        btn_absolute_move.clicked.connect(self.make_absolute_move)

        # We ensure the correct units are shown in the widgets
        self.control_units.buttons()[0].click()

    def create_joystick(self) -> QWidget:
        return ButtonGrid(
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

    def create_units_radio_buttons(self):
        label_units = QLabel('Unidades:')
        radio_mm = QRadioButton('Milímetros')
        radio_in = QRadioButton('Pulgadas')
        self.input_units = QHBoxLayout()
        self.input_units.addWidget(radio_mm)
        self.input_units.addWidget(radio_in)
        self.layout_config.addRow(label_units, self.input_units)
        self.control_units = QButtonGroup()
        self.control_units.addButton(radio_mm, 1)
        self.control_units.addButton(radio_in, 2)
        self.control_units.buttonClicked.connect(self.set_units)

    def create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        return separator

    def create_abs_controls(self):
        # TO DO -> Actualizar limites según la configuración de soft-limits de GRBL
        # (si es que están configurados)
        # $20=0 	Soft limits, boolean
        # $130=200.000 	X Max travel, mm
        # $131=200.000 	Y Max travel, mm
        # $132=200.000 	Z Max travel, mm
        self.input_abs_x = self.create_double_spinbox(0, 200, 0.25, 2)
        self.input_abs_y = self.create_double_spinbox(0, 200, 0.25, 2)
        self.input_abs_z = self.create_double_spinbox(0, 200, 0.25, 2)
        return WidgetsHList([
            QLabel('X: '), self.input_abs_x,
            QLabel('Y: '), self.input_abs_y,
            QLabel('Z: '), self.input_abs_z
        ])

    def set_units(self, button):
        selected_id = self.control_units.id(button)
        self.units = selected_id

        unit_info = self.UNIT_MAPPING[selected_id]

        for input in [
            self.input_x,
            self.input_y,
            self.input_z,
            self.input_abs_x,
            self.input_abs_y,
            self.input_abs_z,
        ]:
            input.setSuffix(unit_info['suffix'])

        self.input_feedrate.setSuffix(unit_info['suffix'] + '/min')

    def create_double_spinbox(
            self,
            limit_low: float,
            limit_high: float,
            step: float,
            precision: int = 2
    ):
        spinbox = QDoubleSpinBox()
        spinbox.setDecimals(precision)
        spinbox.setRange(limit_low, limit_high)
        spinbox.setSingleStep(step)

        return spinbox

    # GRBL controller interaction

    def make_incremental_move(self, x, y, z):
        def send_jog_incremental_move():
            move_x = x * round(self.input_x.value(), 2)
            move_y = y * round(self.input_y.value(), 2)
            move_z = z * round(self.input_z.value(), 2)

            if (move_x == 0 and move_y == 0 and move_z == 0):
                return

            self.send_jog_command(move_x, move_y, move_z, JOG_DISTANCE_INCREMENTAL)
        return send_jog_incremental_move

    def make_absolute_move(self):
        x = round(self.input_abs_x.value(), 2)
        y = round(self.input_abs_y.value(), 2)
        z = round(self.input_abs_z.value(), 2)

        self.send_jog_command(x, y, z, JOG_DISTANCE_ABSOLUTE)

    def send_jog_command(self, x, y, z, distance_mode):
        feedrate = round(self.input_feedrate.value(), 2)
        units_info = self.UNIT_MAPPING[self.units]

        self.grbl_controller.jog(
            x, y, z, feedrate,
            units=units_info['distance_unit'],
            distance_mode=distance_mode
        )
