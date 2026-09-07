import pytest
from manager.adapters.desktop.presentation.components.Joystick import Joystick
from PyQt5.QtWidgets import QDoubleSpinBox, QLabel
from pytest_mock.plugin import MockerFixture
from pytestqt.qtbot import QtBot


class TestJoystick:
    @pytest.fixture(autouse=True)
    def setup_method(self, qtbot: QtBot, mocker: MockerFixture):
        # Mock jog callback
        self.mock_jog_callback = mocker.MagicMock()

        # Inject fakes so Joystick never touches disk or the real singletons
        self.fake_settings = mocker.MagicMock()
        self.fake_settings.jog_step_x = 0.25
        self.fake_settings.jog_step_y = 0.25
        self.fake_settings.jog_step_z = 0.25
        self.fake_settings.jog_feedrate = 200.0
        self.fake_settings.jog_units = 0
        self.mock_config_writer = mocker.MagicMock()

        self.joystick = Joystick(
            settings_reader=self.fake_settings,
            config_writer=self.mock_config_writer,
        )
        self.joystick.set_jog_callback(self.mock_jog_callback)
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
        assert self.joystick.input_x.suffix() == " in"
        assert self.joystick.input_y.suffix() == " in"
        assert self.joystick.input_z.suffix() == " in"
        assert self.joystick.input_feedrate.suffix() == " in/min"

        # Trigger action under test
        self.joystick.control_units.button(0).click()

        # Assertions
        assert self.joystick.units == 0
        assert self.joystick.input_x.suffix() == " mm"
        assert self.joystick.input_y.suffix() == " mm"
        assert self.joystick.input_z.suffix() == " mm"
        assert self.joystick.input_feedrate.suffix() == " mm/min"

    def test_joystick_incremental_move(self, mocker: MockerFixture):
        # Mock widget state
        self.joystick.input_x.setValue(1.5)
        self.joystick.input_y.setValue(1.3)
        self.joystick.input_z.setValue(1.2)
        self.joystick.input_feedrate.setValue(500.0)
        self.joystick.units = 1

        # Mock method
        mock_send_jog_command = mocker.patch.object(Joystick, "send_jog_command")

        # Trigger action under test
        self.joystick.make_incremental_move(1, 1, 1)()

        # Assertions
        mock_send_jog_command.assert_called_once()

        jog_params = {
            "x": 1.5,
            "y": 1.3,
            "z": 1.2,
            "feedrate": 500.0,
            "distance_mode": "distance_incremental",
        }
        mock_send_jog_command.assert_called_with(*jog_params.values())

    def test_joystick_incremental_move_avoids_null_movement(self, mocker: MockerFixture):
        # Mock widget state
        self.joystick.input_x.setValue(1.5)
        self.joystick.input_y.setValue(1.3)
        self.joystick.input_z.setValue(1.2)
        self.joystick.input_feedrate.setValue(500.0)
        self.joystick.units = 1

        # Mock method
        mock_send_jog_command = mocker.patch.object(Joystick, "send_jog_command")

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
        self.joystick.send_jog_command(1.5, 1.3, 1.2, 500.0, "distance_incremental")

        # Assertions — callback receives (x, y, z, feedrate, units, distance_mode)
        self.mock_jog_callback.assert_called_once_with(
            1.5, 1.3, 1.2, 500.0, "milimeters", "distance_incremental"
        )

    def test_joystick_init_widgets_uses_settings(self, mocker: MockerFixture, qtbot: QtBot):
        fake_settings = mocker.MagicMock()
        fake_settings.jog_step_x = 1.11
        fake_settings.jog_step_y = 2.22
        fake_settings.jog_step_z = 3.33
        fake_settings.jog_feedrate = 999.0
        fake_settings.jog_units = 0

        joystick = Joystick(settings_reader=fake_settings, config_writer=mocker.MagicMock())
        qtbot.addWidget(joystick)

        assert joystick.input_x.value() == 1.11
        assert joystick.input_y.value() == 2.22
        assert joystick.input_z.value() == 3.33
        assert joystick.input_feedrate.value() == 999.0

    def test_joystick_set_default_values(self, mocker: MockerFixture, qtbot: QtBot):
        fake_settings = mocker.MagicMock()
        fake_settings.jog_step_x = 0.25
        fake_settings.jog_step_y = 0.25
        fake_settings.jog_step_z = 0.25
        fake_settings.jog_feedrate = 200.0
        fake_settings.jog_units = 0
        mock_writer = mocker.MagicMock()

        joystick = Joystick(settings_reader=fake_settings, config_writer=mock_writer)
        qtbot.addWidget(joystick)

        joystick.input_x.setValue(1.25)
        joystick.input_y.setValue(0.75)
        joystick.input_z.setValue(0.50)
        joystick.input_feedrate.setValue(400.0)
        joystick.control_units.button(0).click()  # units = 0 (mm)

        joystick.set_default_values()

        mock_writer.set_float.assert_any_call("interface.control.jog", "stepx", 1.25)
        mock_writer.set_float.assert_any_call("interface.control.jog", "stepy", 0.75)
        mock_writer.set_float.assert_any_call("interface.control.jog", "stepz", 0.50)
        mock_writer.set_float.assert_any_call("interface.control.jog", "feedrate", 400.0)
        mock_writer.set_int.assert_called_once_with("interface.control.jog", "units", 0)
        mock_writer.save_config.assert_called_once()
