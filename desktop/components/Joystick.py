from config import appConfig
from containers.ButtonGrid import ButtonGrid
from containers.ButtonList import ButtonList
from core.grbl.grblController import GrblController
from core.grbl.grblUtils import JOG_DISTANCE_INCREMENTAL
from mixins.JogController import JogController
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class Joystick(QWidget, JogController):
    def __init__(self, grbl_controller: GrblController, parent=None):
        super(Joystick, self).__init__(parent)
        self.set_controller(grbl_controller)
        self.setup_ui()
        self.init_widgets()

    # UI methods

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Widget structure and components definition

        joystick = self.create_joystick()
        layout.addLayout(joystick)

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

        label_feedrate = QLabel('Avance:')
        # TO DO -> Actualizar feedrate según estado del dispositivo
        # TO DO -> Actualizar max y min feedrate según la configuración de GRBL
        # $110=800.000 (x max rate, mm/min)
        # $111=800.000 (y max rate, mm/min)
        # $112=350.000 (z max rate, mm/min)
        self.input_feedrate = self.create_double_spinbox(0, 1000, 25, 2)
        self.layout_config.addRow(label_feedrate, self.input_feedrate)

        label_units, layout_units = self.create_units_radio_buttons()
        self.layout_config.addRow(label_units, layout_units)

        self.btn_set_default = QPushButton('Establecer por defecto')
        self.btn_set_default.clicked.connect(self.set_default_values)
        self.layout_config.addWidget(self.btn_set_default)

        layout.addLayout(self.layout_config)

    def init_widgets(self):
        step_x = appConfig.get_float('interface.control.jog', 'stepx', 0.0)
        step_y = appConfig.get_float('interface.control.jog', 'stepy', 0.0)
        step_z = appConfig.get_float('interface.control.jog', 'stepz', 0.0)
        feedrate = appConfig.get_float('interface.control.jog', 'feedrate', 0.0)
        units = appConfig.get_int('interface.control.jog', 'units', 0)

        # Set default values
        self.input_x.setValue(step_x)
        self.input_y.setValue(step_y)
        self.input_z.setValue(step_z)
        self.input_feedrate.setValue(feedrate)

        # Set units
        self.control_units.buttons()[units].click()

    def create_joystick(self) -> QVBoxLayout:
        xy_joystick = ButtonGrid(
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
            parent=self
        )

        z_joystick = ButtonList(
            [
                (' Z- ', self.make_incremental_move(0, 0, -1)),
                (' Z+ ', self.make_incremental_move(0, 0, 1)),
            ],
            vertical=False,
            parent=self
        )

        joystick_layout = QVBoxLayout()
        joystick_layout.addWidget(xy_joystick)
        joystick_layout.addWidget(z_joystick)

        return joystick_layout

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

    def set_default_values(self):
        stepx = round(self.input_x.value(), 2)
        stepy = round(self.input_y.value(), 2)
        stepz = round(self.input_z.value(), 2)
        feedrate = round(self.input_feedrate.value(), 2)
        units = self.control_units.checkedId()

        # Set default values
        appConfig.set_float('interface.control.jog', 'stepx', stepx)
        appConfig.set_float('interface.control.jog', 'stepy', stepy)
        appConfig.set_float('interface.control.jog', 'stepz', stepz)
        appConfig.set_float('interface.control.jog', 'feedrate', feedrate)
        appConfig.set_int('interface.control.jog', 'units', units)
        appConfig.save_config()

    # GRBL controller interaction

    def make_incremental_move(self, x, y, z):
        def send_jog_incremental_move():
            move_x = x * round(self.input_x.value(), 2)
            move_y = y * round(self.input_y.value(), 2)
            move_z = z * round(self.input_z.value(), 2)
            feedrate = round(self.input_feedrate.value(), 2)

            if (move_x == 0 and move_y == 0 and move_z == 0):
                return

            self.send_jog_command(
                move_x,
                move_y,
                move_z,
                feedrate,
                JOG_DISTANCE_INCREMENTAL
            )
        return send_jog_incremental_move
