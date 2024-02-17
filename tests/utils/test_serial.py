import pytest
import serial
from utils.serial import SerialService


# Test fixture for setting up and tearing down the SerialService instance
@pytest.fixture
def serial_service():
    service = SerialService()
    yield service
    service.stopConnection()


@pytest.mark.parametrize('open_port', [True, False])
def test_start_connection(serial_service, mocker, open_port: bool):
    # Input values for the startConnection method
    port = 'COMx'
    baudrate = 9600
    timeout = 1

    # Emulate open/closed port
    serial_service.interface.is_open = open_port

    def side_effect_close_port():
        serial_service.interface.is_open = False

    # Mock serial port methods
    mock_close_port = mocker.patch.object(
        serial.Serial,
        'close',
        side_effect=side_effect_close_port
    )
    mock_open_port = mocker.patch.object(serial.Serial, 'open')
    mock_read_port = mocker.patch.object(
        serial.Serial,
        'readline',
        return_value=b'start-message'
    )

    # Call method under test
    serial_service.startConnection(port, baudrate, timeout)

    # Assertions
    assert mock_close_port.call_count == (1 if open_port else 0)
    assert mock_open_port.call_count == 1
    assert mock_read_port.call_count == 1


def test_send_bytes(serial_service, mocker):
    # Sample message with valid G-code
    command = b'?'

    # Mock serial port methods
    mock_write_port = mocker.patch.object(serial.Serial, 'write')

    # Call method under test
    serial_service.sendBytes(command)

    # Assertions
    assert mock_write_port.call_count == 1


def test_send_line(serial_service, mocker):
    # Sample message with valid G-code
    line = 'G1 X10 Y20'

    # Mock serial port methods
    mock_write_port = mocker.patch.object(serial.Serial, 'write')

    # Call method under test
    serial_service.sendLine(line)

    # Assertions
    assert mock_write_port.call_count == 1


@pytest.mark.parametrize('received', ['', 'worked great'])
def test_read_line(serial_service, mocker, received):
    # Mock serial port methods
    mock_read_port = mocker.patch.object(
        serial.Serial,
        'readline',
        return_value=bytes(received, 'utf-8')
    )

    # Call method under test
    response = serial_service.readLine()

    # Assertions
    assert mock_read_port.call_count == 1
    assert response == received


@pytest.mark.parametrize('retries', [0, 1, 2, 3])
def test_read_line_until_message(serial_service, mocker, retries):
    # Mock serial port methods
    mock_read_port = mocker.patch.object(
        serial.Serial,
        'readline',
        side_effect=[b'', b'', b'worked great']
    )

    # Call method under test
    response = serial_service.readLineUntilMessage(max_retries=retries)

    # Assertions
    assert mock_read_port.call_count == (retries + 1 if retries <= 2 else 3)
    assert response == ('' if retries < 2 else 'worked great')


@pytest.mark.parametrize('open_port', [True, False])
def test_stop_connection(serial_service, mocker, open_port: bool):
    # Emulate open/closed port
    serial_service.interface.is_open = open_port

    def side_effect_close_port():
        serial_service.interface.is_open = False

    # Mock serial port methods
    mock_close_port = mocker.patch.object(
        serial.Serial,
        'close',
        side_effect=side_effect_close_port
    )

    # Call method under test
    serial_service.stopConnection()

    # Assertions
    assert mock_close_port.call_count == (1 if open_port else 0)


def test_get_ports(mocker):
    # Mock serial port class method
    mock_list_ports = mocker.patch('serial.tools.list_ports.comports')

    # Call method under test
    SerialService.get_ports()

    # Assertions
    assert mock_list_ports.call_count == 1
