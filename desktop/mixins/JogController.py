from abc import abstractmethod
from core.grbl.grblController import GrblController
from core.grbl.grblUtils import JOG_UNIT_INCHES, JOG_UNIT_MILIMETERS
from PyQt5.QtWidgets import QButtonGroup, QDoubleSpinBox, QHBoxLayout, QLabel, QRadioButton


class JogController():
    UNIT_MAPPING = {
        0: {'suffix': ' mm', 'distance_unit': JOG_UNIT_MILIMETERS},
        1: {'suffix': ' in', 'distance_unit': JOG_UNIT_INCHES}
    }

    def __init__(self):
        # Attributes definition
        self.units = 0  # Default to millimeters

    def set_controller(self, grbl_controller: GrblController):
        self.grbl_controller = grbl_controller

    def create_units_radio_buttons(self) -> tuple[QLabel, QHBoxLayout]:
        label_units = QLabel('Unidades:')
        radio_mm = QRadioButton('Milímetros')
        radio_in = QRadioButton('Pulgadas')

        layout_units = QHBoxLayout()
        layout_units.addWidget(radio_mm)
        layout_units.addWidget(radio_in)

        self.control_units = QButtonGroup()
        self.control_units.addButton(radio_mm, 0)
        self.control_units.addButton(radio_in, 1)
        self.control_units.buttonClicked.connect(self.set_units)

        return label_units, layout_units

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

    def send_jog_command(self, x, y, z, feedrate, distance_mode):
        units_info = self.UNIT_MAPPING[self.units]

        self.grbl_controller.jog(
            x, y, z, feedrate,
            units=units_info['distance_unit'],
            distance_mode=distance_mode
        )

    # Abstract methods

    @abstractmethod
    def set_units(self, _):
        raise NotImplementedError
