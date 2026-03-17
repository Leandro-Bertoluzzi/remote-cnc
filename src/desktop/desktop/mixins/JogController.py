from abc import abstractmethod
from typing import Callable

from core.utilities.grbl.grblUtils import JOG_UNIT_INCHES, JOG_UNIT_MILIMETERS
from PyQt5.QtWidgets import QButtonGroup, QDoubleSpinBox, QHBoxLayout, QLabel, QRadioButton


class JogController:
    UNIT_MAPPING = {
        0: {"suffix": " mm", "distance_unit": JOG_UNIT_MILIMETERS},
        1: {"suffix": " in", "distance_unit": JOG_UNIT_INCHES},
    }

    def __init__(self):
        # Attributes definition
        self.units = 0  # Default to millimeters
        self._jog_callback: Callable[..., None] | None = None

    def set_jog_callback(self, callback: Callable[..., None]) -> None:
        """Register the callable used to send jog commands.

        The callback signature must be::

            callback(x, y, z, feedrate, units, distance_mode)

        :class:`ControlView` supplies a method that delegates to
        ``GatewayClient.send_jog``.
        """
        self._jog_callback = callback

    def create_units_radio_buttons(self) -> tuple[QLabel, QHBoxLayout]:
        label_units = QLabel("Unidades:")
        radio_mm = QRadioButton("Milímetros")
        radio_in = QRadioButton("Pulgadas")

        layout_units = QHBoxLayout()
        layout_units.addWidget(radio_mm)
        layout_units.addWidget(radio_in)

        self.control_units = QButtonGroup()
        self.control_units.addButton(radio_mm, 0)
        self.control_units.addButton(radio_in, 1)
        self.control_units.buttonClicked.connect(self.set_units)

        return label_units, layout_units

    def create_double_spinbox(
        self, limit_low: float, limit_high: float, step: float, precision: int = 2
    ):
        spinbox = QDoubleSpinBox()
        spinbox.setDecimals(precision)
        spinbox.setRange(limit_low, limit_high)
        spinbox.setSingleStep(step)

        return spinbox

    # GRBL controller interaction

    def send_jog_command(self, x, y, z, feedrate, distance_mode):
        units_info = self.UNIT_MAPPING[self.units]

        if self._jog_callback is not None:
            self._jog_callback(x, y, z, feedrate, units_info["distance_unit"], distance_mode)

    # Abstract methods

    @abstractmethod
    def set_units(self, button: object) -> None:
        raise NotImplementedError
