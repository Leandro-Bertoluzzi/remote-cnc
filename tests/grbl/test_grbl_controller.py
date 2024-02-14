from grbl.constants import GRBL_ACTIVE_STATE_IDLE, GRBL_ACTIVE_STATE_RUN, \
    GRBL_ACTIVE_STATE_HOLD, GRBL_ACTIVE_STATE_DOOR, GRBL_ACTIVE_STATE_HOME, \
    GRBL_ACTIVE_STATE_SLEEP, GRBL_ACTIVE_STATE_ALARM, GRBL_ACTIVE_STATE_CHECK
from grbl.grblController import GrblController
from grbl.grblLineParser import GrblLineParser
from grbl.parsers.grblMsgTypes import GRBL_MSG_ALARM, GRBL_MSG_FEEDBACK, GRBL_MSG_HELP, \
    GRBL_MSG_PARAMS, GRBL_MSG_PARSER_STATE, GRBL_MSG_OPTIONS, GRBL_MSG_SETTING, \
    GRBL_MSG_STARTUP, GRBL_MSG_STATUS, GRBL_MSG_VERSION, GRBL_RESULT_ERROR, GRBL_RESULT_OK
from utils.serial import SerialService
from serial import SerialException
import logging
from queue import Queue
import pytest


# Test fixture for setting up and tearing down the SerialService instance
@pytest.fixture
def serial_service():
    service = SerialService()
    yield service
    service.stopConnection()


class TestGrblController:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        grbl_logger = logging.getLogger('test_logger')
        self.grbl_controller = GrblController(grbl_logger)

        # Mock logger methods
        mocker.patch.object(grbl_logger, 'addHandler')
        mocker.patch.object(grbl_logger, 'debug')
        mocker.patch.object(grbl_logger, 'info')
        mocker.patch.object(grbl_logger, 'warning')
        mocker.patch.object(grbl_logger, 'error')
        mocker.patch.object(grbl_logger, 'critical')

    def test_connect_fails_serial(self, mocker):
        # Mock serial methods
        mocker.patch.object(
            SerialService,
            'startConnection',
            side_effect=SerialException('mocked error')
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.connect('test-port', 9600)

        # Assertions
        expected_error_msg = (
            'Failed opening serial port test-port, '
            'verify and close any other connection you may have'
        )
        assert str(error.value) == expected_error_msg

    def test_connect_fails_grbl(self, mocker):
        # Mock serial methods
        mocker.patch.object(SerialService, 'startConnection')
        # Mock GRBL methods
        mocker.patch.object(GrblLineParser, 'parse', return_value=('ANOTHER_CODE', {}))

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.connect('port', 9600)
        assert 'Failed starting connection with GRBL: ' in str(error.value)

    @pytest.mark.parametrize('initial_homing', [False, True])
    def test_connect(self, mocker, initial_homing):
        # Mock serial methods
        mock_serial_connect = mocker.patch.object(SerialService, 'startConnection')
        mocker.patch.object(SerialService, 'readLine')

        second_message = (GRBL_RESULT_OK, {})
        if initial_homing:
            second_message = (
                GRBL_MSG_FEEDBACK, {
                    'message': '\'$H\'|\'$X\' to unlock',
                    'raw': '[MSG:\'$H\'|\'$X\' to unlock]'
                }
            )

        # Mock GRBL methods to receive:
        # Grbl 1.1
        # ok
        # -- or --
        # Grbl 1.1
        # [MSG:'$H'|'$X' to unlock]
        mock_grbl_parser = mocker.patch.object(
            GrblLineParser,
            'parse',
            side_effect=[
                (
                    GRBL_MSG_STARTUP, {
                        'firmware': 'Grbl',
                        'version': '1.1',
                        'message': None,
                        'raw': "Grbl 1.1"
                    }
                ),
                second_message
            ]
        )
        mock_handle_homing = mocker.patch.object(GrblController, 'handleHomingCycle')

        # Call method under test
        response = self.grbl_controller.connect('port', 9600)

        # Assertions
        assert response == {
            'firmware': 'Grbl',
            'version': '1.1',
            'message': None,
            'raw': 'Grbl 1.1'
        }
        assert self.grbl_controller.build_info['version'] == '1.1'
        assert mock_serial_connect.call_count == 1
        assert mock_grbl_parser.call_count == 2
        assert mock_handle_homing.call_count == (1 if initial_homing else 0)

    @pytest.mark.parametrize('connected', [True, False])
    def test_disconnect(self, mocker, connected):
        # Set up controller status for test
        self.grbl_controller.connected = connected
        self.grbl_controller.state['status']['activeState'] = 'CONNECTED'

        # Mock serial methods
        mock_serial_disconnect = mocker.patch.object(SerialService, 'stopConnection')

        # Call method under test
        self.grbl_controller.disconnect()

        # Assertions
        assert mock_serial_disconnect.call_count == (1 if connected else 0)
        assert self.grbl_controller.connected == False
        assert self.grbl_controller.state['status']['activeState'] == (
            'DISCONNECTED' if connected else 'CONNECTED'
        )

    def test_send_command(self):
        # Set up command queue for test
        self.grbl_controller.queue = Queue()

        # Call method under test
        self.grbl_controller.sendCommand('$')

        # Assertions
        assert self.grbl_controller.queue.qsize() == 1
        assert self.grbl_controller.queue.get_nowait() == '$'

    def test_handle_homing_cycle(self, mocker):
        # Mock GRBL methods
        mock_disable_alarm = mocker.patch.object(GrblController, 'disableAlarm')

        # Call the method under test
        self.grbl_controller.handleHomingCycle()

        # Assertions
        assert mock_disable_alarm.call_count == 1

    def test_disable_alarm(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.disableAlarm()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$X')

    def test_query_status_report(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryStatusReport()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('?')

    def test_query_parser_state(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGcodeParserState()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$G')

    def test_query_help(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGrblHelp()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$')

    def test_toggle_checkmode(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.toggleCheckMode()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$C')

    def test_jog(self, mocker):
        # Mock GRBL methods
        mock_build_jog_command = mocker.patch(
            'grbl.grblController.build_jog_command',
            return_value='$J=X1.0 Y2.0 Z3.0 F500.0'
        )
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.jog(1.00, 2.00, 3.00, 500.00)

        # Assertions
        assert mock_build_jog_command.call_count == 1
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$J=X1.0 Y2.0 Z3.0 F500.0')

    def test_set_settings(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.setSettings(
            {
                '$22': '1',
                '$23': '5',
                '$27': '5.200'
            }
        )

        # Assertions
        assert mock_command_send.call_count == 3

    def test_query_build_info(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryBuildInfo()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$I')

    def test_query_settings(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGrblSettings()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$$')

    def test_query_grbl_parameters(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGrblParameters()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$#')

    def test_getters(self):
        # Test values
        mock_machine_position = {'x': '1.000', 'y': '2.000', 'z': '3.000'}
        mock_work_position = {'x': '3.000', 'y': '2.000', 'z': '1.000'}
        mock_modal_group = {
            'motion': 'G0',
            'wcs': 'G54',
            'plane': 'G17',
            'units': 'G21',
            'distance': 'G90',
            'feedrate': 'G94',
            'program': 'M0',
            'spindle': 'M5',
            'coolant': 'M9'
        }
        mock_tool = '7'
        mock_feedrate = '500.0'
        mock_spindle = '50.0'
        mock_parameters = {
            'G54': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G55': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G56': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G57': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G58': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G59': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G28': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G30': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G92': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'TLO': 0.000,
            'PRB': {'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': True}
        }
        mock_checkmode = True

        # Set test values for controller's parameters
        self.grbl_controller.state['status']['mpos'] = mock_machine_position
        self.grbl_controller.state['status']['wpos'] = mock_work_position
        self.grbl_controller.state['parserstate']['modal'] = mock_modal_group
        self.grbl_controller.state['parserstate']['tool'] = mock_tool
        self.grbl_controller.state['parserstate']['feedrate'] = mock_feedrate
        self.grbl_controller.state['parserstate']['spindle'] = mock_spindle
        self.grbl_controller.parameters = mock_parameters
        self.grbl_controller._checkmode = mock_checkmode

        # Call methods under test
        machine_position = self.grbl_controller.getMachinePosition()
        work_position = self.grbl_controller.getWorkPosition()
        modal_group = self.grbl_controller.getModalGroup()
        tool = self.grbl_controller.getTool()
        feedrate = self.grbl_controller.getFeedrate()
        spindle = self.grbl_controller.getSpindle()
        parameters = self.grbl_controller.getParameters()
        checkmode = self.grbl_controller.getCheckModeEnabled()

        # Assertions
        assert machine_position == mock_machine_position
        assert work_position == mock_work_position
        assert modal_group == mock_modal_group
        assert tool == mock_tool
        assert feedrate == mock_feedrate
        assert spindle == mock_spindle
        assert parameters == mock_parameters
        assert checkmode == mock_checkmode

    @pytest.mark.parametrize(
            'active_state',
            [
                GRBL_ACTIVE_STATE_IDLE,
                GRBL_ACTIVE_STATE_RUN,
                GRBL_ACTIVE_STATE_HOLD,
                GRBL_ACTIVE_STATE_DOOR,
                GRBL_ACTIVE_STATE_HOME,
                GRBL_ACTIVE_STATE_SLEEP,
                GRBL_ACTIVE_STATE_ALARM,
                GRBL_ACTIVE_STATE_CHECK
            ]
        )
    def test_checkers(self, active_state):
        # Set test value for controller's active state
        self.grbl_controller.state['status']['activeState'] = active_state

        # Call methods under test
        is_alarm = self.grbl_controller.isAlarm()
        is_idle = self.grbl_controller.isIdle()

        # Assertions
        assert is_alarm == (active_state == GRBL_ACTIVE_STATE_ALARM)
        assert is_idle == (active_state == GRBL_ACTIVE_STATE_IDLE)

    # PARSER

    def test_parser_receive_grbl_parameters(self):
        # Set test values for controller's parameters
        self.grbl_controller.parameters = {}

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse('[G54:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G55:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G56:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G57:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G58:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G59:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G28:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G30:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[G92:0.000,0.000,0.000]', [], [])
        self.grbl_controller.parseResponse('[TLO:0.000]', [], [])
        self.grbl_controller.parseResponse('[PRB:0.000,0.000,0.000:0]', [], [])

        # Assertions
        assert self.grbl_controller.parameters == {
            'G54': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G55': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G56': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G57': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G58': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G59': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G28': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G30': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'G92': {'x': 0.000, 'y': 0.000, 'z': 0.000},
            'TLO': 0.000,
            'PRB': {'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': False}
        }

    def test_parser_receive_grbl_settings(self):
        # Set test values for controller's settings
        self.grbl_controller.settings = {}

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse('$0=100.200', [], [])
        self.grbl_controller.parseResponse('$102=1.000', [], [])

        # Assertions
        assert self.grbl_controller.settings == {
            '$0': {
                'value': '100.200',
                'message': 'Step pulse time',
                'units': 'microseconds',
                'description': 'Sets time length per step. Minimum 3usec.'
            },
            '$102': {
                'value': '1.000',
                'message': 'Z-axis travel resolution',
                'units': 'step/mm',
                'description': 'Z-axis travel resolution in steps per millimeter.'
            }
        }

    @pytest.mark.parametrize(
            'messages,expected',
            [
                (
                    [
                        '[VER:1.1d.20161014:]',
                        '[OPT:VL,15,128]'
                    ],
                    {
                        'version': '1.1d.20161014',
                        'comment': '',
                        'optionCode': 'VL',
                        'blockBufferSize': 15,
                        'rxBufferSize': 128
                    }
                ),
                (
                    [
                        '[OPT:VL,15,128]'
                    ],
                    {
                        'optionCode': 'VL',
                        'blockBufferSize': 15,
                        'rxBufferSize': 128
                    }
                ),
                (
                    [
                        '[VER:1.1d.20161014:]'
                    ],
                    {
                        'version': '1.1d.20161014',
                        'comment': ''
                    }
                )
            ]
        )
    def test_parser_receive_grbl_build_info(self, messages, expected):
        # Set test values for controller's settings
        self.grbl_controller.build_info = {}

        # Simulate getting responses from GRBL
        for message in messages:
            self.grbl_controller.parseResponse(message, [], [])

        # Assertions
        assert self.grbl_controller.build_info == expected

    @pytest.mark.parametrize(
            'message,previous_state,expected_state',
            [
                ('[MSG:Enabled]', False, True),
                ('[MSG:Disabled]', True, False),
                ('[MSG:Enabled]', True, True),
                ('[MSG:Disabled]', False, False)
            ]
        )
    def test_parser_receive_checkmode_feedback(self, message, previous_state, expected_state):
        # Set test values for controller's status
        self.grbl_controller._checkmode == previous_state

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse(message, [], [])

        # Assertions
        assert self.grbl_controller._checkmode == expected_state

    def test_parser_receive_help(self):
        # Set test values for controller's status
        self.grbl_controller.help_text = ''

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse(
            '[HLP:$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x]',
            [],
            []
        )

        # Assertions
        assert self.grbl_controller.help_text == (
            '$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x'
        )

    def test_parser_receive_parser_state(self):
        # Set test values for controller's status
        self.grbl_controller.state['parserstate'] = {
            'modal': {
                'motion': 'G0',
                'wcs': 'G54',
                'plane': 'G17',
                'units': 'G21',
                'distance': 'G90',
                'feedrate': 'G94',
                'program': 'M0',
                'spindle': 'M5',
                'coolant': 'M9'
            },
            'tool': 1,
            'feedrate': 0.0,
            'spindle': 0.0
        }

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse(
            '[GC:G38.2 G54 G17 G21 G91 G94 M0 M5 M7 M8 T0 F20. S0.]',
            [],
            []
        )

        # Assertions
        expected_parser_state = {
            'modal': {
                'motion': 'G38.2',
                'wcs': 'G54',
                'plane': 'G17',
                'units': 'G21',
                'distance': 'G91',
                'feedrate': 'G94',
                'program': 'M0',
                'spindle': 'M5',
                'coolant': ['M7', 'M8']
            },
            'tool': 0,
            'feedrate': 20.0,
            'spindle': 0.0
        }
        assert self.grbl_controller.state['parserstate'] == expected_parser_state

    def test_parser_receive_status_report(self):
        # Set test values for controller's status
        self.grbl_controller.state['status'] = {
            'activeState': '',
            'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'ov': []
        }

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse(
            '<Idle|MPos:5.000,2.000,0.000|FS:0,0|Ov:100,100,100>',
            [],
            []
        )

        # Assertions
        new_status = {
            'activeState': 'Idle',
            'mpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'feedrate': 0.0,
            'spindle': 0,
            'ov': [100, 100, 100]
        }
        assert self.grbl_controller.state['status'] == new_status

    def test_parser_receive_disable_alarm_feedback(self):
        # Set test values for controller's status
        self.grbl_controller._alarm = True

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse('[MSG:Caution: Unlocked]', [], [])

        # Assertions
        assert self.grbl_controller._alarm == False
