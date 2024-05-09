from grbl.grblController import GrblController
from grbl.grblLineParser import GrblLineParser
from grbl.grblMonitor import GrblMonitor
from grbl.grblStatus import GrblStatus
from grbl.parsers.grblMsgTypes import GRBL_MSG_FEEDBACK, GRBL_MSG_STARTUP, GRBL_RESULT_OK
import mocks.grbl_mocks as grbl_mocks
from utils.serial import SerialService
from serial import SerialException
import logging
from queue import Empty, Queue
import pytest
from pytest_mock.plugin import MockerFixture
import threading
import time


# Test fixture for setting up and tearing down the SerialService instance
@pytest.fixture
def serial_service():
    service = SerialService()
    yield service
    service.stopConnection()


class TestGrblController:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker: MockerFixture):
        grbl_logger = logging.getLogger('test_logger')
        self.grbl_controller = GrblController(grbl_logger)
        self.grbl_status = self.grbl_controller.grbl_status

        # Mock logger methods
        mocker.patch.object(GrblMonitor, 'debug')
        mocker.patch.object(GrblMonitor, 'info')
        mocker.patch.object(GrblMonitor, 'warning')
        mocker.patch.object(GrblMonitor, 'error')
        mocker.patch.object(GrblMonitor, 'critical')
        mocker.patch.object(GrblMonitor, 'sent')
        mocker.patch.object(GrblMonitor, 'received')

    def test_connect_fails_serial(self, mocker: MockerFixture):
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

    def test_connect_fails_grbl(self, mocker: MockerFixture):
        # Mock serial methods
        mocker.patch.object(SerialService, 'startConnection')
        # Mock GRBL methods
        mocker.patch.object(GrblLineParser, 'parse', return_value=('ANOTHER_CODE', {}))

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.connect('port', 9600)
        assert 'Failed starting connection with GRBL: ' in str(error.value)

    @pytest.mark.parametrize('initial_homing', [False, True])
    def test_connect(self, mocker: MockerFixture, initial_homing):
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

        # Mock thread
        mock_thread_create = mocker.patch.object(threading.Thread, '__init__', return_value=None)
        mock_thread_start = mocker.patch.object(threading.Thread, 'start')

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
        assert mock_thread_create.call_count == 1
        assert mock_thread_start.call_count == 1

    @pytest.mark.parametrize('connected', [True, False])
    def test_disconnect(self, mocker: MockerFixture, connected):
        # Mock GRBL status methods
        mocker.patch.object(
            self.grbl_status,
            'connected',
            return_value=connected
        )
        mock_set_active_state = mocker.patch.object(self.grbl_status, 'set_active_state')

        # Mock serial methods
        mock_serial_disconnect = mocker.patch.object(SerialService, 'stopConnection')

        # Call method under test
        self.grbl_controller.disconnect()

        # Assertions
        assert mock_serial_disconnect.call_count == (1 if connected else 0)
        assert self.grbl_controller.grbl_status._flags['connected'] is False
        assert mock_set_active_state.call_count == (1 if connected else 0)

    @pytest.mark.parametrize('paused', [False, True])
    def test_set_paused(self, mocker: MockerFixture, paused):
        # Mock other methods from controller
        mock_pause = mocker.patch.object(self.grbl_controller, 'grbl_pause')
        mock_resume = mocker.patch.object(self.grbl_controller, 'grbl_resume')

        # Call method under test
        self.grbl_controller.setPaused(paused)

        # Assertions
        assert self.grbl_status.paused() == paused
        assert mock_pause.call_count == (1 if paused else 0)
        assert mock_resume.call_count == (0 if paused else 1)

    def test_send_command(self):
        # Set up command queue for test
        self.grbl_controller.queue = Queue()

        # Call method under test
        self.grbl_controller.sendCommand('$')

        # Assertions
        assert self.grbl_controller.queue.qsize() == 1
        assert self.grbl_controller.queue.get_nowait() == '$'

    def test_handle_homing_cycle(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_disable_alarm = mocker.patch.object(GrblController, 'disableAlarm')

        # Call the method under test
        self.grbl_controller.handleHomingCycle()

        # Assertions
        assert mock_disable_alarm.call_count == 1

    def test_disable_alarm(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.disableAlarm()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$X')

    def test_query_status_report(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(SerialService, 'sendBytes')

        # Call the method under test
        self.grbl_controller.queryStatusReport()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with(b'?')

    def test_query_status_report_error(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(
            SerialService,
            'sendBytes',
            side_effect=SerialException('mocked-error')
        )

        # Mock monitor methods
        mock_monitor_error = mocker.patch.object(GrblMonitor, 'error')

        # Call the method under test
        self.grbl_controller.queryStatusReport()

        # Assertions
        assert mock_command_send.call_count == 1
        assert mock_monitor_error.call_count == 1

    def test_query_parser_state(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGcodeParserState()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$G')

    def test_query_help(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGrblHelp()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$')

    def test_toggle_checkmode(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.toggleCheckMode()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$C')

    def test_jog(self, mocker: MockerFixture):
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

    def test_set_settings(self, mocker: MockerFixture):
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

    def test_query_build_info(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryBuildInfo()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$I')

    def test_query_settings(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGrblSettings()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$$')

    def test_query_grbl_parameters(self, mocker: MockerFixture):
        # Mock GRBL methods
        mock_command_send = mocker.patch.object(GrblController, 'sendCommand')

        # Call the method under test
        self.grbl_controller.queryGrblParameters()

        # Assertions
        assert mock_command_send.call_count == 1
        mock_command_send.assert_called_with('$#')

    def test_getters(self):
        # Set test values for controller's parameters
        self.grbl_controller.parameters = grbl_mocks.grbl_parameters
        self.grbl_controller.settings = grbl_mocks.grbl_settings
        self.grbl_controller.build_info = grbl_mocks.grbl_build_info

        # Call methods under test
        parameters = self.grbl_controller.getParameters()
        settings = self.grbl_controller.getGrblSettings()
        build_info = self.grbl_controller.getBuildInfo()

        # Assertions
        assert parameters == grbl_mocks.grbl_parameters
        assert settings == grbl_mocks.grbl_settings
        assert build_info == grbl_mocks.grbl_build_info

    @pytest.mark.parametrize(
        'occupied,expected',
        [
            (0, 0.0),
            (16, 12.5),
            (32, 25.0),
            (64, 50.0),
            (128, 100.0)
        ]
    )
    def test_get_buffer_fill(self, occupied, expected):
        # Set test value for controller's active state
        self.grbl_controller._sumcline = occupied

        # Call methods under test
        value = self.grbl_controller.getBufferFill()

        # Assertions
        assert value == expected

    def test_empty_command_queue(self, mocker: MockerFixture):
        # Mock queue contents
        self.grbl_controller.queue.put('Command 1')
        self.grbl_controller.queue.put('Command 2')
        self.grbl_controller.queue.put('Command 3')

        # Spy queue methods
        mock_queue_size = mocker.spy(Queue, 'qsize')
        mock_queue_get = mocker.spy(Queue, 'get_nowait')

        # Call method under test
        self.grbl_controller.emptyQueue()

        # Assertions
        assert mock_queue_size.call_count == 4
        assert mock_queue_get.call_count == 3

    def test_empty_command_queue_empty(self, mocker: MockerFixture):
        # Mock queue methods
        mock_queue_size = mocker.patch.object(Queue, 'qsize', return_value=1)
        mock_queue_get = mocker.patch.object(Queue, 'get_nowait', side_effect=Empty())

        # Call method under test
        self.grbl_controller.emptyQueue()

        # Assertions
        assert mock_queue_size.call_count == 1
        assert mock_queue_get.call_count == 1

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
        'message,expected_state',
        [
            ('[MSG:Enabled]', True),
            ('[MSG:Disabled]', False)
        ]
    )
    def test_parser_receive_checkmode_feedback(
        self,
        mocker: MockerFixture,
        message,
        expected_state
    ):
        # Mock monitor methods
        mock_monitor_info = mocker.patch.object(GrblMonitor, 'info')

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse(message, [], [])

        # Assertions
        assert mock_monitor_info.call_count == 1
        mock_monitor_info.assert_called_with(
            f'Checkmode was successfully updated to {expected_state}'
        )

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

    def test_parser_receive_parser_state(self, mocker: MockerFixture):
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
        assert self.grbl_status._state['parserstate'] == expected_parser_state

    def test_parser_receive_status_report(self):
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
            'ov': [100, 100, 100],
            'subState': None,
            'wco': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'pinstate': None,
            'buffer': None,
            'line': None,
            'accessoryState': None
        }
        assert self.grbl_controller.grbl_status._state['status'] == new_status

    def test_parser_receive_disable_alarm_feedback(self):
        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse('[MSG:Caution: Unlocked]', [], [])

        # Assertions
        assert self.grbl_status.is_alarm() is False

    def test_parser_receive_ok(self):
        # Set test values
        cline = [1, 2, 3]
        sline = ['$H', 'G54', 'G00 X0 Y0']
        self.grbl_controller._sumcline = 6  # sum([1, 2, 3])

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse('ok', cline, sline)

        # Assertions
        assert cline == [2, 3]
        assert sline == ['G54', 'G00 X0 Y0']
        assert self.grbl_controller._sumcline == 5

    def test_parser_receive_error(self, mocker: MockerFixture):
        # Set test values
        cline = [1, 2, 3]
        sline = ['G54 G54', 'G90', 'G00 X0 Y0']

        # Mock status methods
        mock_set_error = mocker.patch.object(GrblStatus, 'set_error')

        # Mock monitor methods
        mock_monitor_error = mocker.patch.object(GrblMonitor, 'error')

        # Mock other methods
        mock_pause = mocker.patch.object(self.grbl_controller, 'grbl_pause')

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse('error:25', cline, sline)

        # Assertions
        assert cline == [2, 3]
        assert sline == ['G90', 'G00 X0 Y0']
        assert mock_set_error.call_count == 1
        mock_set_error.assert_called_with(
            'G54 G54',
            {
                'code': 25,
                'message': 'Invalid gcode ID:25',
                'description': 'Repeated g-code word found in block.'
            }
        )
        assert mock_monitor_error.call_count == 1
        mock_monitor_error.assert_called_with(
            'Error: Invalid gcode ID:25. Description: Repeated g-code word found in block.'
        )
        assert mock_pause.call_count == 1
        assert self.grbl_status.paused() is True

    def test_parser_receive_alarm(self, mocker: MockerFixture):
        # Set test values
        cline = [1, 2, 3]
        sline = ['$H', 'G54', 'G00 X0 Y0']

        # Mock status methods
        mock_set_error = mocker.patch.object(GrblStatus, 'set_error')

        # Mock monitor methods
        mock_monitor_critical = mocker.patch.object(GrblMonitor, 'critical')

        # Simulate getting responses from GRBL
        self.grbl_controller.parseResponse('ALARM:6', cline, sline)

        # Assertions
        assert cline == [2, 3]
        assert sline == ['G54', 'G00 X0 Y0']
        assert mock_set_error.call_count == 1
        mock_set_error.assert_called_with(
            '$H',
            {
                'code': 6,
                'message': 'Homing fail',
                'description': 'Homing fail. The active homing cycle was reset.'
            }
        )
        assert self.grbl_status._flags['alarm'] is True
        assert mock_monitor_critical.call_count == 1
        mock_monitor_critical.assert_called_with(
            'Alarm activated: Homing fail. Description: Homing fail. '
            'The active homing cycle was reset.'
        )
        assert self.grbl_status.paused() is True

    # SERIAL I/O

    @pytest.mark.parametrize('paused', [True, False])
    def test_serial_io(self, mocker: MockerFixture, paused):
        # **Test case description (no pause)**
        # Round 1: query status + get command to send + read line + parse line + send command
        # Round 2: query status + get command to send + send command
        # Round 3: query status + read line (no response)

        # Mock attributes
        self.grbl_controller.serial_thread = threading.Thread()

        # Mock queue contents
        self.grbl_controller.queue.put('Command 1')
        self.grbl_controller.queue.put('Command 2')

        # Mock time and thread life cycle
        self.count = 0
        self.current_time = 1703991600.0    # 2023-12-31 03:00:00.3 (UTC)

        def manage_time():
            # Manage thread
            if self.count == 3:
                self.grbl_controller.serial_thread = None
            self.count = self.count + 1

            # Fake time, adding 200 ms each time
            new_time = self.current_time
            self.current_time = self.current_time + 0.2
            return new_time

        # Mock timer method
        mock_time = mocker.patch.object(
            time,
            'time',
            side_effect=manage_time
        )

        # Mock status methods
        mocker.patch.object(GrblStatus, 'paused', return_value=paused)

        # Mock controller methods
        mock_query_status_report = mocker.patch.object(GrblController, 'queryStatusReport')
        mock_parse_response = mocker.patch.object(GrblController, 'parseResponse')

        # Mock serial methods
        mock_serial_waiting = mocker.patch.object(
            SerialService,
            'waiting',
            side_effect=[True, False, True]
        )
        mock_serial_read_line = mocker.patch.object(
            SerialService,
            'readLine',
            side_effect=['test message', '', '']
        )
        mock_serial_send_line = mocker.patch.object(SerialService, 'sendLine')

        # Mock monitor methods
        mock_monitor_sent = mocker.patch.object(GrblMonitor, 'sent')

        # Spy queue methods
        spy_queue_size = mocker.spy(Queue, 'qsize')
        spy_queue_get = mocker.spy(Queue, 'get_nowait')

        # Call method under test
        self.grbl_controller.serialIO()

        # Assertions
        # **Query GRBL status section**
        assert mock_time.call_count == 4
        assert mock_query_status_report.call_count == 3
        # **Read serial section**
        assert mock_serial_waiting.call_count == 3
        assert mock_serial_read_line.call_count == (3 if paused else 2)
        assert mock_parse_response.call_count == 1
        # **Write serial section**
        assert spy_queue_size.call_count == (0 if paused else 3)
        assert spy_queue_get.call_count == (0 if paused else 2)
        assert mock_serial_send_line.call_count == (0 if paused else 2)
        assert mock_monitor_sent.call_count == (0 if paused else 2)

    @pytest.mark.parametrize(
        'error_read,error_send',
        [
            (True, False),
            (False, True)
        ]
    )
    def test_serial_io_serial_error(self, mocker: MockerFixture, error_read, error_send):
        # Mock attributes
        self.grbl_controller.serial_thread = threading.Thread()

        # Mock queue contents
        self.grbl_controller.queue.put('Command')

        # Mock controller methods
        mocker.patch.object(GrblController, 'queryStatusReport')
        mock_disconnect = mocker.patch.object(GrblController, 'disconnect')
        mock_parse_response = mocker.patch.object(GrblController, 'parseResponse')

        # Mock serial methods
        mock_serial_waiting = mocker.patch.object(
            SerialService,
            'waiting',
            return_value=error_read
        )
        mock_serial_read_line = mocker.patch.object(
            SerialService,
            'readLine',
            side_effect=SerialException('mocked-error')
        )
        mock_serial_send_line = mocker.patch.object(
            SerialService,
            'sendLine',
            side_effect=SerialException('mocked-error')
        )

        # Mock status methods
        mocker.patch.object(GrblStatus, 'paused', return_value=False)

        # Mock monitor methods
        mock_monitor_error = mocker.patch.object(GrblMonitor, 'error')

        # Call method under test
        self.grbl_controller.serialIO()

        # Assertions
        assert mock_serial_waiting.call_count == 1
        assert mock_serial_read_line.call_count == (1 if error_read else 0)
        assert mock_serial_send_line.call_count == (1 if error_send else 0)
        assert mock_parse_response.call_count == 0
        assert mock_monitor_error.call_count == 1
        assert mock_disconnect.call_count == 1

    def test_serial_io_stop(self, mocker: MockerFixture):
        # Mock attributes
        self.grbl_controller.serial_thread = threading.Thread()
        self.grbl_controller.grbl_status._flags['stop'] = True

        # Mock thread life cycle
        def stop_thread():
            self.grbl_controller.serial_thread = None

        # Mock controller methods
        mocker.patch.object(GrblController, 'queryStatusReport')

        # Mock serial methods
        mocker.patch.object(SerialService, 'waiting', return_value=False)
        mocker.patch.object(SerialService, 'readLine', return_value='')

        # Mock status methods
        mocker.patch.object(GrblStatus, 'paused', return_value=False)

        # Mock monitor methods
        mocker.patch.object(GrblController, 'emptyQueue', side_effect=stop_thread)
        mock_monitor_info = mocker.patch.object(GrblMonitor, 'info')

        # Call method under test
        self.grbl_controller.serialIO()

        # Assertions
        assert mock_monitor_info.call_count == 1
        assert self.grbl_controller.grbl_status._flags['stop'] is False

    def test_serial_io_query_parser_state(self, mocker: MockerFixture):
        # Mock attributes
        self.grbl_controller.serial_thread = threading.Thread()

        # Mock queue contents
        self.grbl_controller.queue.put('Command 1')

        # Mock time
        self.current_time = 1703991600.0    # 2023-12-31 03:00:00.3 (UTC)

        def manage_time():
            # Fake time, adding 15 s each time
            new_time = self.current_time
            self.current_time = self.current_time + 15.0
            return new_time

        # Mock timer method
        mock_time = mocker.patch.object(
            time,
            'time',
            side_effect=manage_time
        )

        # Mock thread life cycle
        def stop_thread():
            self.grbl_controller.serial_thread = None

        # Mock controller methods
        mocker.patch.object(GrblController, 'queryStatusReport')
        mock_query_parser_state = mocker.patch.object(
            GrblController,
            'queryGcodeParserState',
            side_effect=stop_thread
        )

        # Mock serial methods
        mocker.patch.object(SerialService, 'waiting', return_value=False)
        mocker.patch.object(SerialService, 'readLine', return_value='')
        mocker.patch.object(SerialService, 'sendLine')

        # Mock status methods
        mocker.patch.object(GrblStatus, 'paused', return_value=False)

        # Mock monitor methods
        mocker.patch.object(GrblMonitor, 'sent')

        # Call method under test
        self.grbl_controller.serialIO()

        # Assertions
        assert mock_time.call_count == 2
        assert mock_query_parser_state.call_count == 1

    def test_serial_io_query_buffer_full(self, mocker: MockerFixture):
        # Mock attributes
        self.grbl_controller.serial_thread = threading.Thread()

        # Mock queue contents
        self.grbl_controller.queue.put('Command 1')

        # Mock thread life cycle
        def stop_thread():
            self.grbl_controller.serial_thread = None
            return False

        # Mock builtin 'sum' fucntion
        mock_sum = mocker.patch('builtins.sum', return_value=500)

        # Mock controller methods
        mocker.patch.object(GrblController, 'queryStatusReport')

        # Mock serial methods
        mocker.patch.object(SerialService, 'waiting', side_effect=stop_thread)
        mocker.patch.object(SerialService, 'readLine', return_value='')
        mock_send_line = mocker.patch.object(SerialService, 'sendLine')

        # Mock status methods
        mocker.patch.object(GrblStatus, 'paused', return_value=False)

        # Mock monitor methods
        mock_monitor_sent = mocker.patch.object(GrblMonitor, 'sent')

        # Call method under test
        self.grbl_controller.serialIO()

        # Assertions
        assert mock_sum.call_count == 1
        assert mock_send_line.call_count == 0
        assert mock_monitor_sent.call_count == 0

    def test_serial_io_end_command(self, mocker: MockerFixture):
        # Mock attributes
        self.grbl_controller.serial_thread = threading.Thread()

        # Mock queue contents
        self.grbl_controller.queue.put('Command 1')
        self.grbl_controller.queue.put('M30')

        # Mock controller methods
        mocker.patch.object(GrblController, 'queryStatusReport')

        # Mock serial methods
        mocker.patch.object(SerialService, 'waiting', return_value=False)
        mock_serial_send_line = mocker.patch.object(SerialService, 'sendLine')

        # Mock status methods
        mocker.patch.object(GrblStatus, 'paused', return_value=False)

        # Mock monitor methods
        mock_monitor_info = mocker.patch.object(GrblMonitor, 'info')

        # Call method under test
        self.grbl_controller.serialIO()

        # Assertions
        assert mock_serial_send_line.call_count == 2
        assert mock_monitor_info.call_count == 1
        mock_monitor_info.assert_called_with('A program end command was found: M30')
        assert self.grbl_controller.grbl_status._flags['finished'] is True
