from grbl.constants import GRBL_ACTIVE_STATE_IDLE, GRBL_ACTIVE_STATE_RUN, GRBL_ACTIVE_STATE_HOLD, GRBL_ACTIVE_STATE_DOOR, \
    GRBL_ACTIVE_STATE_HOME, GRBL_ACTIVE_STATE_SLEEP, GRBL_ACTIVE_STATE_ALARM, GRBL_ACTIVE_STATE_CHECK
from grbl.grblController import GrblController
from grbl.grblLineParser import GrblLineParser
from grbl.parsers.grblMsgTypes import GRBL_MSG_ALARM, GRBL_MSG_FEEDBACK, GRBL_MSG_STARTUP, GRBL_RESULT_OK, GRBL_RESULT_ERROR
from utils.serial import SerialService
from serial import SerialException
import pytest

# Test fixture for setting up and tearing down the SerialService instance
@pytest.fixture
def serial_service():
    service = SerialService()
    yield service
    service.stopConnection()

class TestGrblController:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.grbl_controller = GrblController()

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
        # Mock serial methods
        mock_serial_stream = mocker.patch.object(SerialService, 'streamLine')
        mock_serial_read = mocker.patch.object(SerialService, 'readLine')
        # Mock GRBL methods
        mock_grbl_parser = mocker.patch.object(
            GrblLineParser,
            'parse',
            side_effect=[
                (GRBL_MSG_FEEDBACK, {'message': 'Caution: Unlocked', 'raw': '[MSG:Caution: Unlocked]'}),
                (GRBL_RESULT_OK, {})
            ]
        )

        # Call the method under test
        response = self.grbl_controller.handleHomingCycle()

        # Assertions
        assert response
        assert mock_serial_stream.call_count == 1
        assert mock_serial_read.call_count == 1
        assert mock_grbl_parser.call_count == 2

    def test_handle_homing_cycle_fails(self, mocker):
        # Mock serial methods
        mock_serial_stream = mocker.patch.object(SerialService, 'streamLine')
        mock_serial_read = mocker.patch.object(SerialService, 'readLine')
        # Mock GRBL methods
        mock_grbl_parser = mocker.patch.object(
            GrblLineParser,
            'parse',
            side_effect=[
                (GRBL_MSG_FEEDBACK, {'message': 'Caution: Unlocked', 'raw': '[MSG:Caution: Unlocked]'}),
                ('ANOTHER_CODE', {})
            ]
        )

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            self.grbl_controller.handleHomingCycle()

        # Assertions
        assert str(error.value) == 'There was an error handling the homing cycle.'
        assert mock_serial_stream.call_count == 1
        assert mock_serial_read.call_count == 1
        assert mock_grbl_parser.call_count == 2

    def test_getters(self):
        # Test values
        mock_machine_position = { 'x': '1.000', 'y': '2.000', 'z': '3.000' }
        mock_work_position = { 'x': '3.000', 'y': '2.000', 'z': '1.000' }
        mock_modal_group = { 'motion': 'G0', 'wcs': 'G54', 'plane': 'G17', 'units': 'G21', 'distance': 'G90', 'feedrate': 'G94', 'program': 'M0', 'spindle': 'M5', 'coolant': 'M9' }
        mock_tool = '7'
        mock_parameters = {
            'G54' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G55' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G56' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G57' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G58' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G59' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G28' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G30' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'G92' : { 'x': '0.000', 'y': '0.000', 'z': '0.000' },
            'TLO' : 0.000,
            'PRB' : { 'x': '0.000', 'y': '0.000', 'z': '0.000', 'result': True }
        }

        # Set test values for controller's parameters
        self.grbl_controller.state['status']['mpos'] = mock_machine_position
        self.grbl_controller.state['status']['wpos'] = mock_work_position
        self.grbl_controller.state['parserstate']['modal'] = mock_modal_group
        self.grbl_controller.state['parserstate']['tool'] = mock_tool
        self.grbl_controller.settings['parameters'] = mock_parameters

        # Call methods under test
        machine_position = self.grbl_controller.getMachinePosition()
        work_position = self.grbl_controller.getWorkPosition()
        modal_group = self.grbl_controller.getModalGroup()
        tool = self.grbl_controller.getTool()
        parameters = self.grbl_controller.getParameters()

        # Assertions
        assert machine_position == mock_machine_position
        assert work_position == mock_work_position
        assert modal_group == mock_modal_group
        assert tool == mock_tool
        assert parameters == mock_parameters

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
    def test_checkers(self, mocker, active_state):
        # Set test value for controller's active state
        self.grbl_controller.state['status']['activeState'] = active_state

        # Call methods under test
        is_alarm = self.grbl_controller.isAlarm()
        is_idle = self.grbl_controller.isIdle()

        # Assertions
        assert is_alarm == (active_state == GRBL_ACTIVE_STATE_ALARM)
        assert is_idle == (active_state == GRBL_ACTIVE_STATE_IDLE)
