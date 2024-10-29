from desktop.components.Joystick import Joystick
from PyQt5.QtWidgets import QDoubleSpinBox, QLabel
import pytest


class TestJoystick:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        # Mock GRBL controller object
        self.grbl_controller = mocker.MagicMock()

        # Create an instance of Joystick
        self.joystick = Joystick(self.grbl_controller)
        qtbot.addWidget(self.joystick)

    def test_joystick_init(self, helpers):
        # Validate amount of each type of widget
        assert helpers.count_widgets(self.joystick.layout_config, QLabel) == 5
        assert helpers.count_widgets(self.joystick.layout_config, QDoubleSpinBox) == 4

    def test_joystick_set_units(self):
        # Mock attributes
        self.joystick.units = 0

        # Trigger action under test
        self.joystick.control_units.button(1).click()

        # Assertions
        assert self.joystick.units == 1
        assert self.joystick.input_x.suffix() == ' in'
        assert self.joystick.input_y.suffix() == ' in'
        assert self.joystick.input_z.suffix() == ' in'
        assert self.joystick.input_feedrate.suffix() == ' in/min'

        # Trigger action under test
        self.joystick.control_units.button(0).click()

        # Assertions
        assert self.joystick.units == 0
        assert self.joystick.input_x.suffix() == ' mm'
        assert self.joystick.input_y.suffix() == ' mm'
        assert self.joystick.input_z.suffix() == ' mm'
        assert self.joystick.input_feedrate.suffix() == ' mm/min'

    def test_joystick_incremental_move(self, mocker):
        # Mock widget state
        self.joystick.input_x.setValue(1.5)
        self.joystick.input_y.setValue(1.3)
        self.joystick.input_z.setValue(1.2)
        self.joystick.input_feedrate.setValue(500.0)
        self.joystick.units = 1

        # Mock method
        mock_send_jog_command = mocker.patch.object(Joystick, 'send_jog_command')

        # Trigger action under test
        self.joystick.make_incremental_move(1, 1, 1)()

        # Assertions
        mock_send_jog_command.assert_called_once()

        jog_params = {
            'x': 1.5,
            'y': 1.3,
            'z': 1.2,
            'feedrate': 500.0,
            'distance_mode': 'distance_incremental'
        }
        mock_send_jog_command.assert_called_with(*jog_params.values())

    def test_joystick_incremental_move_avoids_null_movement(self, mocker):
        # Mock widget state
        self.joystick.input_x.setValue(1.5)
        self.joystick.input_y.setValue(1.3)
        self.joystick.input_z.setValue(1.2)
        self.joystick.input_feedrate.setValue(500.0)
        self.joystick.units = 1

        # Mock method
        mock_send_jog_command = mocker.patch.object(Joystick, 'send_jog_command')

        # Trigger action under test
        self.joystick.make_incremental_move(0, 0, 0)()

        # Mock widget state
        self.joystick.input_x.setValue(0)
        self.joystick.input_y.setValue(0)
        self.joystick.input_z.setValue(0)

        # Trigger action under test
        self.joystick.make_incremental_move(1, 1, 1)()

        # Assertions
        assert mock_send_jog_command.call_count == 0

    def test_send_jog_command(self):
        # Mock widget state
        self.joystick.input_feedrate.setValue(500.0)
        self.joystick.units = 0

        # Trigger action under test
        self.joystick.send_jog_command(1.5, 1.3, 1.2, 500.0, 'distance_incremental')

        # Assertions
        self.grbl_controller.jog.assert_called_once()

        jog_params = {
            'x': 1.5,
            'y': 1.3,
            'z': 1.2,
            'feedrate': 500.0
        }
        self.grbl_controller.jog.assert_called_with(
            *jog_params.values(),
            units='milimeters',
            distance_mode='distance_incremental'
        )
