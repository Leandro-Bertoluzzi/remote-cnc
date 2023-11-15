from containers.ButtonGrid import ButtonGrid
from components.JogController import JogController
from PyQt5.QtWidgets import QDoubleSpinBox, QLabel, QRadioButton
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
        assert helpers.count_widgets_with_type(self.jog_controller.layout(), ButtonGrid) == 1
        assert helpers.count_widgets_with_type(self.jog_controller.form_layout, QLabel) == 5
        assert helpers.count_widgets_with_type(self.jog_controller.form_layout, QDoubleSpinBox) == 4
        assert helpers.count_widgets_with_type(self.jog_controller.input_units, QRadioButton) == 2

    def test_jog_controller_set_step_x(self):
        # Mock attributes
        self.jog_controller.step_x = 0.00

        # Trigger action under test
        self.jog_controller.input_x.setValue(2.522)

        # Assertions
        assert self.jog_controller.step_x == 2.52

    def test_jog_controller_set_step_y(self):
        # Mock attributes
        self.jog_controller.step_y = 0.00

        # Trigger action under test
        self.jog_controller.input_y.setValue(2.522)

        # Assertions
        assert self.jog_controller.step_y == 2.52

    def test_jog_controller_set_step_z(self):
        # Mock attributes
        self.jog_controller.step_z = 0.00

        # Trigger action under test
        self.jog_controller.input_z.setValue(2.522)

        # Assertions
        assert self.jog_controller.step_z == 2.52

    def test_jog_controller_set_feedrate(self):
        # Mock attributes
        self.jog_controller.feedrate = 0.00

        # Trigger action under test
        self.jog_controller.input_feedrate.setValue(252.203)

        # Assertions
        assert self.jog_controller.feedrate == 252.20

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
        # Mock attributes
        self.jog_controller.step_x = 1.5
        self.jog_controller.step_y = 1.3
        self.jog_controller.step_z = 1.2
        self.jog_controller.feedrate = 500.0
        self.jog_controller.units = 'mm'

        # Mock GRBL controller method
        attrs = {
            'build_jog_command.return_value': 'jog_command',
            'streamLine.return_value': {'raw': 'ok'},
        }
        self.grbl_controller.configure_mock(**attrs)

        # Trigger action under test
        self.jog_controller.make_incremental_move(1, 1, 1)()

        # Assertions
        self.grbl_controller.build_jog_command.assert_called_once()
        self.grbl_controller.streamLine.assert_called_once()

        jog_params = {
            'x': 1.5,
            'y': 1.3,
            'z': 1.2,
            'feedrate': 500.0
        }
        self.grbl_controller.build_jog_command.assert_called_with(*jog_params.values(), units='milimeters', distance_mode='distance_incremental')
        self.grbl_controller.streamLine.assert_called_with('jog_command', 'jog command')
