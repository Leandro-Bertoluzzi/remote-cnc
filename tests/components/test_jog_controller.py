from components.JogController import JogController
from containers.ButtonGrid import ButtonGrid
from containers.WidgetsHList import WidgetsHList
from PyQt5.QtWidgets import QDoubleSpinBox, QLabel, QPushButton, QRadioButton
import pytest


class TestJogController:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        # Mock GRBL controller object
        self.grbl_controller = mocker.MagicMock()

        # Mock terminal method
        self.mock_grbl_log = mocker.Mock()

        # Create an instance of JogController
        self.jog_controller = JogController(self.grbl_controller, self.mock_grbl_log)
        qtbot.addWidget(self.jog_controller)

    def test_jog_controller_init(self, helpers):
        # Validate amount of each type of widget
        assert helpers.count_widgets(self.jog_controller.layout(), ButtonGrid) == 1
        assert helpers.count_widgets(self.jog_controller.layout(), WidgetsHList) == 1
        assert helpers.count_widgets(self.jog_controller.layout(), QPushButton) == 1
        assert helpers.count_widgets(self.jog_controller.layout_config, QLabel) == 5
        assert helpers.count_widgets(self.jog_controller.layout_config, QDoubleSpinBox) == 4
        assert helpers.count_widgets(self.jog_controller.input_units, QRadioButton) == 2

    def test_jog_controller_set_units(self):
        # Mock attributes
        self.jog_controller.units = 'mm'

        # Trigger action under test
        self.jog_controller.control_units.button(2).click()

        # Assertions
        assert self.jog_controller.units == 'in'
        assert self.jog_controller.input_x.suffix() == ' in'
        assert self.jog_controller.input_y.suffix() == ' in'
        assert self.jog_controller.input_z.suffix() == ' in'
        assert self.jog_controller.input_feedrate.suffix() == ' in/min'

        # Trigger action under test
        self.jog_controller.control_units.button(1).click()

        # Assertions
        assert self.jog_controller.units == 'mm'
        assert self.jog_controller.input_x.suffix() == ' mm'
        assert self.jog_controller.input_y.suffix() == ' mm'
        assert self.jog_controller.input_z.suffix() == ' mm'
        assert self.jog_controller.input_feedrate.suffix() == ' mm/min'

    def test_jog_controller_incremental_move(self, mocker):
        # Mock widget state
        self.jog_controller.input_x.setValue(1.5)
        self.jog_controller.input_y.setValue(1.3)
        self.jog_controller.input_z.setValue(1.2)
        self.jog_controller.input_feedrate.setValue(500.0)
        self.jog_controller.units = 'mm'

        # Mock method
        mock_send_jog_command = mocker.patch.object(JogController, 'send_jog_command')

        # Trigger action under test
        self.jog_controller.make_incremental_move(1, 1, 1)()

        # Assertions
        mock_send_jog_command.assert_called_once()

        jog_params = {
            'x': 1.5,
            'y': 1.3,
            'z': 1.2,
            'distance_mode': 'distance_incremental'
        }
        mock_send_jog_command.assert_called_with(*jog_params.values())

    def test_jog_controller_incremental_move_avoids_null_movement(self, mocker):
        # Mock widget state
        self.jog_controller.input_x.setValue(1.5)
        self.jog_controller.input_y.setValue(1.3)
        self.jog_controller.input_z.setValue(1.2)
        self.jog_controller.input_feedrate.setValue(500.0)
        self.jog_controller.units = 'mm'

        # Mock method
        mock_send_jog_command = mocker.patch.object(JogController, 'send_jog_command')

        # Trigger action under test
        self.jog_controller.make_incremental_move(0, 0, 0)()

        # Mock widget state
        self.jog_controller.input_x.setValue(0)
        self.jog_controller.input_y.setValue(0)
        self.jog_controller.input_z.setValue(0)

        # Trigger action under test
        self.jog_controller.make_incremental_move(1, 1, 1)()

        # Assertions
        assert mock_send_jog_command.call_count == 0

    def test_jog_controller_absolute_move(self, mocker):
        # Mock widget state
        self.jog_controller.input_abs_x.setValue(1.5)
        self.jog_controller.input_abs_y.setValue(1.3)
        self.jog_controller.input_abs_z.setValue(1.2)
        self.jog_controller.input_feedrate.setValue(500.0)
        self.jog_controller.units = 'mm'

        # Mock method
        mock_send_jog_command = mocker.patch.object(JogController, 'send_jog_command')

        # Trigger action under test
        self.jog_controller.make_absolute_move()

        # Assertions
        mock_send_jog_command.assert_called_once()

        jog_params = {
            'x': 1.5,
            'y': 1.3,
            'z': 1.2,
            'distance_mode': 'distance_absolute'
        }
        mock_send_jog_command.assert_called_with(*jog_params.values())

    def test_send_jog_command(self):
        # Mock widget state
        self.jog_controller.input_feedrate.setValue(500.0)
        self.jog_controller.units = 'mm'

        # Mock GRBL controller method
        attrs = {
            'build_jog_command.return_value': 'jog_command',
            'streamLine.return_value': {'raw': 'ok'},
        }
        self.grbl_controller.configure_mock(**attrs)

        # Trigger action under test
        self.jog_controller.send_jog_command(1.5, 1.3, 1.2, 'distance_absolute')

        # Assertions
        self.grbl_controller.build_jog_command.assert_called_once()
        self.grbl_controller.streamLine.assert_called_once()

        jog_params = {
            'x': 1.5,
            'y': 1.3,
            'z': 1.2,
            'feedrate': 500.0
        }
        self.grbl_controller.build_jog_command.assert_called_with(
            *jog_params.values(),
            units='milimeters',
            distance_mode='distance_absolute'
        )
        self.grbl_controller.streamLine.assert_called_with('jog_command', 'jog command')
