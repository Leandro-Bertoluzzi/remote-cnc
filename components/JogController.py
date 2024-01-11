from containers.ButtonGrid import ButtonGrid
from containers.WidgetsHList import WidgetsHList
from core.grbl.grblController import GrblController, GRBL_LINE_JOG, JOG_DISTANCE_ABSOLUTE, \
    JOG_DISTANCE_INCREMENTAL, JOG_UNIT_INCHES, JOG_UNIT_MILIMETERS
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QButtonGroup, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, \
    QLabel, QMessageBox, QPushButton, QRadioButton, QSizePolicy, QVBoxLayout, QWidget
from typing import Callable


class JogController(QWidget):
    def __init__(
            self,
            grbl_controller: GrblController,
            grbl_log: Callable[[str], None],
            parent=None
    ):
        super(JogController, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # Attributes definition
        self.grbl_controller = grbl_controller
        self.grbl_log = grbl_log

        # State management
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

        layout.addLayout(self.layout_config)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(separator)

        label_absolute = QLabel('Mover a posición (absoluta): ')
        layout.addWidget(label_absolute)
        # TO DO -> Actualizar limites según la configuración de soft-limits de GRBL
        # (si es que están configurados)
        # $20=0 	Soft limits, boolean
        # $130=200.000 	X Max travel, mm
        # $131=200.000 	Y Max travel, mm
        # $132=200.000 	Z Max travel, mm
        self.input_abs_x = self.create_double_spinbox(0, 200, 0.25, 2)
        self.input_abs_y = self.create_double_spinbox(0, 200, 0.25, 2)
        self.input_abs_z = self.create_double_spinbox(0, 200, 0.25, 2)
        self.abs_controls = WidgetsHList([
            QLabel('X: '),
            self.input_abs_x,
            QLabel('Y: '),
            self.input_abs_y,
            QLabel('Z: '),
            self.input_abs_z
        ])
        layout.addWidget(self.abs_controls)
        btn_absolute_move = QPushButton('Mover')
        btn_absolute_move.clicked.connect(self.make_absolute_move)
        layout.addWidget(btn_absolute_move)

        # We ensure the correct units are shown in the widgets
        radio_mm.click()

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
        self.input_abs_x.setSuffix(' ' + self.units)
        self.input_abs_y.setSuffix(' ' + self.units)
        self.input_abs_z.setSuffix(' ' + self.units)

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
        units = JOG_UNIT_MILIMETERS if self.units == 'mm' else JOG_UNIT_INCHES

        jog_command = self.grbl_controller.build_jog_command(
            x, y, z, feedrate,
            units=units,
            distance_mode=distance_mode
        )
        self.grbl_log(jog_command)

        try:
            response = self.grbl_controller.streamLine(jog_command, GRBL_LINE_JOG)
            self.grbl_log(response['raw'])
        except Exception as error:
            QMessageBox.critical(
                self,
                'Error',
                str(error),
                QMessageBox.Ok
            )

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
