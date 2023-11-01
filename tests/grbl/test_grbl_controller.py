from grbl.constants import GRBL_ACTIVE_STATE_IDLE, GRBL_ACTIVE_STATE_RUN, GRBL_ACTIVE_STATE_HOLD, GRBL_ACTIVE_STATE_DOOR, \
    GRBL_ACTIVE_STATE_HOME, GRBL_ACTIVE_STATE_SLEEP, GRBL_ACTIVE_STATE_ALARM, GRBL_ACTIVE_STATE_CHECK
from grbl.grblController import GrblController
from grbl.grblLineParser import GrblLineParser
from grbl.parsers.grblMsgTypes import *
from utils.serial import SerialService
from serial import SerialException
import logging
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
        mocker.patch.object(SerialService, 'startConnection', side_effect=SerialException('mocked error'))

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.connect('port', 9600)
        assert str(error.value) == 'Failed opening serial port, verify the connection and close any other connection you may have'

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
            second_message = (GRBL_MSG_FEEDBACK, {'message': '\'$H\'|\'$X\' to unlock', 'raw': '[MSG:\'$H\'|\'$X\' to unlock]'})

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
                (GRBL_MSG_STARTUP, {'firmware': 'Grbl', 'version': '1.1', 'message': None, 'raw': "Grbl 1.1"}),
                second_message
            ]
        )
        mock_handle_homing = mocker.patch.object(GrblController, 'handleHomingCycle')

        # Call method under test
        response = self.grbl_controller.connect('port', 9600)

        # Assertions
        assert response == {'firmware': 'Grbl', 'version': '1.1', 'message': None, 'raw': "Grbl 1.1"}
        assert self.grbl_controller.settings['version'] == '1.1'
        assert mock_serial_connect.call_count == 1
        assert mock_grbl_parser.call_count == 2
        assert mock_handle_homing.call_count == (1 if initial_homing else 0)

    def test_disconnect(self, mocker):
        # Mock serial methods
        mock_serial_disconnect = mocker.patch.object(SerialService, 'stopConnection')

        # Call method under test
        self.grbl_controller.disconnect()

        # Assertions
        assert mock_serial_disconnect.call_count == 1

    def test_stream_line(self, mocker):
        # Mock serial methods
        mock_serial_stream = mocker.patch.object(SerialService, 'streamLine')
        # Mock GRBL methods
        mock_grbl_parser = mocker.patch.object(GrblLineParser, 'parse', return_value=(GRBL_RESULT_OK, {}))

        # Call method under test
        response = self.grbl_controller.streamLine('a line of code')

        # Assertions
        assert response == {}
        assert mock_serial_stream.call_count == 1
        assert mock_grbl_parser.call_count == 1

    @pytest.mark.parametrize(
            'messages,amount',
            [
                (
                    [
                        (GRBL_MSG_FEEDBACK, {'message': 'A message', 'raw': '[MSG: A message]'}),
                        (GRBL_RESULT_OK, {'raw': 'ok'})
                    ],
                    2
                ),
                (
                    [
                        ('ANOTHER_CODE', {}),
                        (GRBL_MSG_HELP, {'message': 'help message...', 'raw': '[HLP: help message...]'}),
                        (GRBL_RESULT_OK, {'raw': 'ok'})
                    ],
                    3
                ),
                (
                    [
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        (GRBL_MSG_FEEDBACK, {'message': 'A message', 'raw': '[MSG: A message]'}),
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        (GRBL_RESULT_OK, {'raw': 'ok'})
                    ],
                    6
                ),
                (
                    [
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        (GRBL_MSG_FEEDBACK, {'message': 'A message', 'raw': '[MSG: A message]'}),
                        (GRBL_RESULT_OK, {'raw': 'ok'}),
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        (GRBL_RESULT_OK, {'raw': 'ok'})
                    ],
                    4
                )
            ]
        )
    def test_send_command(self, mocker, messages, amount):
        # Mock serial methods
        mock_serial_send = mocker.patch.object(SerialService, 'sendLine')
        mock_serial_read = mocker.patch.object(SerialService, 'readLine')
        # Mock GRBL methods
        mock_grbl_parser = mocker.patch.object(GrblLineParser, 'parse', side_effect=messages)

        # Call method under test
        self.grbl_controller.sendCommand('$')

        # Assertions
        assert mock_serial_send.call_count == 1
        assert mock_serial_read.call_count == amount
        assert mock_grbl_parser.call_count == amount

    def test_send_command_invalid(self, mocker):
        # Mock serial methods
        mock_serial_send = mocker.patch.object(SerialService, 'sendLine')

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.sendCommand('INVALID')

        # Assertions
        assert str(error.value) == 'Invalid GRBL command: INVALID'
        assert mock_serial_send.call_count == 0

    def test_send_command_fails(self, mocker):
        # Mock serial methods
        mock_serial_send = mocker.patch.object(SerialService, 'sendLine')
        mock_serial_read = mocker.patch.object(SerialService, 'readLine')
        # Mock GRBL methods
        mock_grbl_parser = mocker.patch.object(
            GrblLineParser,
            'parse',
            side_effect=[
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                (GRBL_MSG_FEEDBACK, {'message': 'A message', 'raw': '[MSG: A message]'}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                (GRBL_RESULT_OK, {'raw': 'ok'})
            ]
        )

        MESSAGES_LIMIT = 15

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.sendCommand('$')

        # Assertions
        assert str(error.value) == 'There was an error processing the command: $'
        assert mock_serial_send.call_count == 1
        assert mock_serial_read.call_count == MESSAGES_LIMIT
        assert mock_grbl_parser.call_count == MESSAGES_LIMIT

    def test_stream_line_error(self, mocker):
        # Mock serial methods
        mock_serial_stream = mocker.patch.object(SerialService, 'streamLine')
        # Mock GRBL methods
        mock_grbl_parser = mocker.patch.object(
            GrblLineParser,
            'parse',
            return_value=(GRBL_RESULT_ERROR, {'code': '99', 'message': 'An error', 'description': 'An error happened.', 'raw': 'error:99'})
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.streamLine('a line of code')

        # Assertions
        assert str(error.value) == 'Error executing line: An error. Description: An error happened.'
        assert mock_serial_stream.call_count == 1
        assert mock_grbl_parser.call_count == 1

    def test_stream_line_alarm(self, mocker):
        # Mock serial methods
        mock_serial_stream = mocker.patch.object(SerialService, 'streamLine')
        # Mock GRBL methods
        mock_grbl_parser = mocker.patch.object(
            GrblLineParser,
            'parse',
            return_value=(GRBL_MSG_ALARM, {'code': '99', 'message': 'An alarm', 'description': 'An alarm was triggered.', 'raw': 'error:99'})
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.streamLine('a line of code')

        # Assertions
        assert str(error.value) == 'Alarm activated: An alarm. Description: An alarm was triggered.'
        assert mock_serial_stream.call_count == 1
        assert mock_grbl_parser.call_count == 1

    def test_handle_homing_cycle(self, mocker):
        # Mock GRBL methods
        mock_disable_alarm = mocker.patch.object(GrblController, 'disableAlarm')

        # Call the method under test
        self.grbl_controller.handleHomingCycle()

        # Assertions
        assert mock_disable_alarm.call_count == 1

    def test_disable_alarm(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                (GRBL_MSG_FEEDBACK, {'message': 'Caution: Unlocked', 'raw': '[MSG:Caution: Unlocked]'}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test
        response = self.grbl_controller.disableAlarm()

        # Assertions
        assert response == 'Alarm was successfully disabled'
        assert mock_command_send.call_count == 1

    def test_disable_alarm_no_alarm(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test
        response = self.grbl_controller.disableAlarm()

        # Assertions
        assert response == 'There is no alarm to disable'
        assert mock_command_send.call_count == 1

    def test_disable_alarm_fails(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                ('ANOTHER_CODE', {}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.disableAlarm()

        # Assertions
        assert str(error.value) == 'There was an error disabling the alarm'
        assert mock_command_send.call_count == 1

    def test_query_status_report(self, mocker):
        # Test values
        self.grbl_controller.state['status'] = {
            'activeState': '',
            'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'ov': []
        }
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                (
                    GRBL_MSG_STATUS,
                    {
                        'activeState': 'Idle',
                        'mpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
                        'feedrate': 0.0,
                        'spindle': 0,
                        'ov': [100, 100, 100],
                        'raw': '<Idle|MPos:5.000,2.000,0.000|FS:0,0|Ov:100,100,100>'
                    }
                ),
                (GRBL_RESULT_OK, {})
            ]
        )

        new_status = {
            'activeState': 'Idle',
            'mpos': {'x': 5.0, 'y': 2.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'feedrate': 0.0,
            'spindle': 0,
            'ov': [100, 100, 100],
            'raw': '<Idle|MPos:5.000,2.000,0.000|FS:0,0|Ov:100,100,100>'
        }

        # Call the method under test
        response = self.grbl_controller.queryStatusReport()

        # Assertions
        assert response == new_status
        assert self.grbl_controller.state['status'] == new_status
        assert mock_command_send.call_count == 1

    def test_query_status_report_fails(self, mocker):
        # Test values
        old_status = {
            'activeState': '',
            'mpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'wpos': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'ov': []
        }
        self.grbl_controller.state['status'] = old_status
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.queryStatusReport()

        # Assertions
        assert str(error.value) == 'There was an error retrieving the device status'
        assert self.grbl_controller.state['status'] == old_status
        assert mock_command_send.call_count == 1

    def test_query_parser_state(self, mocker):
        # Test values
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
            'tool': '',
            'feedrate': '',
            'spindle': ''
        }
        new_parser_state = {
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
            'tool': '0',
            'feedrate': '20.',
            'spindle': '0.',
            'raw': '[GC:G38.2 G54 G17 G21 G91 G94 M0 M5 M7 M8 T0 F20. S0.]'
        }
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                (
                    GRBL_MSG_PARSER_STATE,
                    new_parser_state
                ),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test
        response = self.grbl_controller.queryGcodeParserState()

        # Assertions
        assert response == new_parser_state
        assert self.grbl_controller.state['parserstate'] == new_parser_state
        assert mock_command_send.call_count == 1

    def test_query_parser_state_fails(self, mocker):
        # Test values
        old_parser_state = {
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
            'tool': '',
            'feedrate': '',
            'spindle': ''
        }
        self.grbl_controller.state['parserstate'] = old_parser_state
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                ('ANOTHER_CODE', {}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.queryGcodeParserState()

        # Assertions
        assert str(error.value) == 'There was an error retrieving the parser state'
        assert self.grbl_controller.state['parserstate'] == old_parser_state
        assert mock_command_send.call_count == 1

    def test_query_help(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                (GRBL_MSG_HELP, {'message': '$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x', 'raw': '[HLP:$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x]'}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test
        response = self.grbl_controller.queryGrblHelp()

        # Assertions
        assert response == {'message': '$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x', 'raw': '[HLP:$$ $# $G $I $N $x=val $Nx=line $J=line $C $X $H ~ ! ? ctrl-x]'}
        assert mock_command_send.call_count == 1

    def test_query_help_fails(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_values=[
                ('ANOTHER_CODE', {}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.queryGrblHelp()

        # Assertions
        assert str(error.value) == 'There was an error executing the help command'
        assert mock_command_send.call_count == 1

    @pytest.mark.parametrize(
            'message,previous_state,expected_state',
            [
                ('Enabled', False, True),
                ('Disabled', True, False),
                ('Enabled', True, True),
                ('Disabled', False, False)
            ]
        )
    def test_toggle_checkmode(self, mocker, message, previous_state, expected_state):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                (GRBL_MSG_FEEDBACK, {'message': message}),
                (GRBL_RESULT_OK, {})
            ]
        )
        # Set test values for controller's parameters
        self.grbl_controller.settings['checkmode'] = previous_state

        # Call the method under test
        response = self.grbl_controller.toggleCheckMode()

        # Assertions
        assert self.grbl_controller.settings['checkmode'] == expected_state
        assert response == {'checkmode': expected_state }
        assert mock_command_send.call_count == 1

    @pytest.mark.parametrize(
            'messages',
            [
                (
                    [
                        (GRBL_MSG_FEEDBACK, {'message': 'An unexpected message'}),
                        (GRBL_RESULT_OK, {})
                    ]
                ),
                (
                    [
                        ('ANOTHER_CODE', {}),
                        (GRBL_RESULT_OK, {})
                    ]
                ),
                (
                    [
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        (GRBL_MSG_FEEDBACK, {'message': 'An unexpected message'}),
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        (GRBL_RESULT_OK, {})
                    ]
                )
            ]
        )
    def test_toggle_checkmode_fails(self, mocker, messages):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand', return_value=messages)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.toggleCheckMode()

        # Assertions
        assert str(error.value) == 'There was an error enabling the check mode'
        assert mock_command_send.call_count == 1

    @pytest.mark.parametrize(
            'messages,expected',
            [
                (
                    [
                        (GRBL_MSG_VERSION, {'version': '1.1d.20161014', 'comment': '', 'raw': '[VER:1.1d.20161014:]'}),
                        (GRBL_MSG_OPTIONS, {'optionCode': 'VL', 'blockBufferSize': '15', 'rxBufferSize': '128', 'raw': '[OPT:VL,15,128]'}),
                        (GRBL_RESULT_OK, {})
                    ],
                    {'version': '1.1d.20161014', 'comment': '', 'raw_version': '[VER:1.1d.20161014:]', 'optionCode': 'VL', 'blockBufferSize': '15', 'rxBufferSize': '128', 'raw_option': '[OPT:VL,15,128]'}
                ),
                (
                    [
                        (GRBL_MSG_OPTIONS, {'optionCode': 'VL', 'blockBufferSize': '15', 'rxBufferSize': '128', 'raw': '[OPT:VL,15,128]'}),
                        (GRBL_RESULT_OK, {})
                    ],
                    {'optionCode': 'VL', 'blockBufferSize': '15', 'rxBufferSize': '128', 'raw_option': '[OPT:VL,15,128]'}
                ),
                (
                    [
                        (GRBL_MSG_VERSION, {'version': '1.1d.20161014', 'comment': '', 'raw': '[VER:1.1d.20161014:]'}),
                        (GRBL_RESULT_OK, {})
                    ],
                    {'version': '1.1d.20161014', 'comment': '', 'raw_version': '[VER:1.1d.20161014:]'}
                )
            ]
        )
    def test_query_build_info(self, mocker, messages, expected):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=messages
        )

        # Call the method under test
        response = self.grbl_controller.queryBuildInfo()

        # Assertions
        assert response == expected
        assert mock_command_send.call_count == 1

    def test_query_build_info_fails(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.queryBuildInfo()

        # Assertions
        assert str(error.value) == 'There was an error retrieving the build info'
        assert mock_command_send.call_count == 1

    @pytest.mark.parametrize(
            'messages,expected',
            [
                (
                    [
                        (GRBL_MSG_SETTING, {'name': '$0', 'value': '100.200', 'raw': '$0=100.200'}),
                        (GRBL_MSG_SETTING, {'name': '$102', 'value': '1.000', 'raw': '$102=1.000'}),
                        (GRBL_RESULT_OK, {})
                    ],
                    {
                        '$0': {
                            'value' : '100.200',
                            'message': 'Step pulse time',
                            'units': 'microseconds',
                            'description': 'Sets time length per step. Minimum 3usec.'
                        },
                        '$102': {
                            'value' : '1.000',
                            'message': 'Z-axis travel resolution',
                            'units': 'step/mm',
                            'description': 'Z-axis travel resolution in steps per millimeter.'
                        }
                    }
                ),
                (
                    [
                        (GRBL_MSG_SETTING, {'name': '$0', 'value': '100.200', 'raw': '$0=100.200'}),
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        ('ANOTHER_CODE', {}),
                        (GRBL_MSG_SETTING, {'name': '$102', 'value': '1.000', 'raw': '$102=1.000'}),
                        (GRBL_RESULT_OK, {})
                    ],
                    {
                        '$0': {
                            'value' : '100.200',
                            'message': 'Step pulse time',
                            'units': 'microseconds',
                            'description': 'Sets time length per step. Minimum 3usec.'
                        },
                        '$102': {
                            'value' : '1.000',
                            'message': 'Z-axis travel resolution',
                            'units': 'step/mm',
                            'description': 'Z-axis travel resolution in steps per millimeter.'
                        }
                    }
                )
            ]
        )
    def test_query_settings(self, mocker, messages, expected):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=messages
        )

        # Call the method under test
        response = self.grbl_controller.queryGrblSettings()

        # Assertions
        assert response == expected
        assert mock_command_send.call_count == 1

    def test_query_settings_fails(self, mocker):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                ('ANOTHER_CODE', {}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.queryGrblSettings()

        # Assertions
        assert str(error.value) == 'There was an error retrieving the GRBL settings'
        assert mock_command_send.call_count == 1

    def test_query_grbl_parameters(self, mocker):
        # Set test values for controller's parameters
        self.grbl_controller.settings['parameters'] = {}

        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            GrblController,
            'sendCommand',
            return_value=[
                (GRBL_MSG_PARAMS, {'name': 'G54', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G54:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G55', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G55:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G56', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G56:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G57', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G57:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G58', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G58:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G59', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G59:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G28', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G28:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G30', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G30:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'G92', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000}, 'raw': '[G92:0.000,0.000,0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'TLO', 'value': 0.000, 'raw': '[TLO:0.000]'}),
                (GRBL_MSG_PARAMS, {'name': 'PRB', 'value': {'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': False}, 'raw': '[PRB:0.000,0.000,0.000:0]'}),
            ]
        )

        # Call the method under test
        response = self.grbl_controller.queryGrblParameters()

        # Assertions
        assert response == {
            'G54' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G55' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G56' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G57' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G58' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G59' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G28' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G30' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G92' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'TLO' : 0.000,
            'PRB' : { 'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': False }
        }
        assert mock_command_send.call_count == 1

    def test_getters(self):
        # Test values
        mock_machine_position = { 'x': '1.000', 'y': '2.000', 'z': '3.000' }
        mock_work_position = { 'x': '3.000', 'y': '2.000', 'z': '1.000' }
        mock_modal_group = { 'motion': 'G0', 'wcs': 'G54', 'plane': 'G17', 'units': 'G21', 'distance': 'G90', 'feedrate': 'G94', 'program': 'M0', 'spindle': 'M5', 'coolant': 'M9' }
        mock_tool = '7'
        mock_parameters = {
            'G54' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G55' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G56' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G57' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G58' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G59' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G28' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G30' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'G92' : { 'x': 0.000, 'y': 0.000, 'z': 0.000 },
            'TLO' : 0.000,
            'PRB' : { 'x': 0.000, 'y': 0.000, 'z': 0.000, 'result': True }
        }
        mock_checkmode = True

        # Set test values for controller's parameters
        self.grbl_controller.state['status']['mpos'] = mock_machine_position
        self.grbl_controller.state['status']['wpos'] = mock_work_position
        self.grbl_controller.state['parserstate']['modal'] = mock_modal_group
        self.grbl_controller.state['parserstate']['tool'] = mock_tool
        self.grbl_controller.settings['parameters'] = mock_parameters
        self.grbl_controller.settings['checkmode'] = mock_checkmode

        # Call methods under test
        machine_position = self.grbl_controller.getMachinePosition()
        work_position = self.grbl_controller.getWorkPosition()
        modal_group = self.grbl_controller.getModalGroup()
        tool = self.grbl_controller.getTool()
        parameters = self.grbl_controller.getParameters()
        checkmode = self.grbl_controller.getCheckModeEnabled()

        # Assertions
        assert machine_position == mock_machine_position
        assert work_position == mock_work_position
        assert modal_group == mock_modal_group
        assert tool == mock_tool
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
