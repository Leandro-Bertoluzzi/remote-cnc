from desktop.components.dialogs.AbsoluteMoveDialog import AbsoluteMoveDialog
import pytest


class TestAbsoluteMoveDialog:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot, mocker):
        # Mock GRBL controller object
        self.grbl_controller = mocker.MagicMock()

        # Create an instance of AbsoluteMoveDialog
        self.dialog = AbsoluteMoveDialog(self.grbl_controller)
        qtbot.addWidget(self.dialog)

    def test_material_data_dialog_get_inputs(self, qtbot):
        self.dialog.input_x.setValue(20.0)
        self.dialog.input_y.setValue(25.0)
        self.dialog.input_z.setValue(30.0)
        self.dialog.input_feedrate.setValue(200.0)

        assert self.dialog.getInputs() == (20.0, 25.0, 30.0, 200.0)

    def test_move_dialog_set_units(self):
        # Mock attributes
        self.dialog.units = 0

        # Trigger action under test
        self.dialog.control_units.button(1).click()

        # Assertions
        assert self.dialog.units == 1
        assert self.dialog.input_x.suffix() == ' in'
        assert self.dialog.input_y.suffix() == ' in'
        assert self.dialog.input_z.suffix() == ' in'
        assert self.dialog.input_feedrate.suffix() == ' in/min'

        # Trigger action under test
        self.dialog.control_units.button(0).click()

        # Assertions
        assert self.dialog.units == 0
        assert self.dialog.input_x.suffix() == ' mm'
        assert self.dialog.input_y.suffix() == ' mm'
        assert self.dialog.input_z.suffix() == ' mm'
        assert self.dialog.input_feedrate.suffix() == ' mm/min'

    def test_move_dialog_incremental_move(self, mocker):
        # Mock widget state
        self.dialog.input_x.setValue(1.5)
        self.dialog.input_y.setValue(1.3)
        self.dialog.input_z.setValue(1.2)
        self.dialog.input_feedrate.setValue(500.0)
        self.dialog.units = 1

        # Mock method
        mock_send_jog_command = mocker.patch.object(AbsoluteMoveDialog, 'send_jog_command')

        # Trigger action under test
        self.dialog.make_absolute_move()

        # Assertions
        mock_send_jog_command.assert_called_once()

        jog_params = {
            'x': 1.5,
            'y': 1.3,
            'z': 1.2,
            'feedrate': 500.0,
            'distance_mode': 'distance_absolute'
        }
        mock_send_jog_command.assert_called_with(*jog_params.values())

    def test_send_jog_command(self):
        # Mock widget state
        self.dialog.input_feedrate.setValue(500.0)
        self.dialog.units = 0

        # Trigger action under test
        self.dialog.send_jog_command(1.5, 1.3, 1.2, 500.0, 'distance_absolute')

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
            distance_mode='distance_absolute'
        )
