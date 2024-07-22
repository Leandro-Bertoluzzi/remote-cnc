import pytest
from pytest_mock.plugin import MockerFixture
import serial
from utils.serial import SerialService


@pytest.mark.parametrize('open_port', [True, False])
def test_start_connection(mocker: MockerFixture, open_port):
    # Input values for the startConnection method
    port = 'COMx'
    baudrate = 9600
    timeout = 1

    # Emulate open/closed port
    serial_service = SerialService()
    serial_service.interface.is_open = open_port

    def side_effect_close_port():
        nonlocal serial_service
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


def test_send_bytes(mocker: MockerFixture):
    # Sample message with valid G-code
    command = b'?'

    # Mock serial port methods
    mock_write_port = mocker.patch.object(serial.Serial, 'write')

    # Call method under test
    serial_service = SerialService()
    serial_service.sendBytes(command)

    # Assertions
    assert mock_write_port.call_count == 1


def test_send_line(mocker: MockerFixture):
    # Sample message with valid G-code
    line = 'G1 X10 Y20'

    # Mock serial port methods
    mock_write_port = mocker.patch.object(serial.Serial, 'write')

    # Call method under test
    serial_service = SerialService()
    serial_service.sendLine(line)

    # Assertions
    assert mock_write_port.call_count == 1


@pytest.mark.parametrize('received', ['', 'worked great'])
def test_read_line(mocker: MockerFixture, received):
    # Mock serial port methods
    mock_read_port = mocker.patch.object(
        serial.Serial,
        'readline',
        return_value=bytes(received, 'utf-8')
    )

    # Call method under test
    serial_service = SerialService()
    response = serial_service.readLine()

    # Assertions
    assert mock_read_port.call_count == 1
    assert response == received


@pytest.mark.parametrize('retries', [0, 1, 2, 3])
def test_read_line_until_message(mocker: MockerFixture, retries):
    # Mock serial port methods
    mock_read_port = mocker.patch.object(
        serial.Serial,
        'readline',
        side_effect=[b'', b'', b'worked great']
    )

    # Call method under test
    serial_service = SerialService()
    response = serial_service.readLineUntilMessage(max_retries=retries)

    # Assertions
    assert mock_read_port.call_count == (retries + 1 if retries <= 2 else 3)
    assert response == ('' if retries < 2 else 'worked great')


@pytest.mark.parametrize('open_port', [True, False])
def test_stop_connection(mocker: MockerFixture, open_port):
    # Emulate open/closed port
    serial_service = SerialService()
    serial_service.interface.is_open = open_port

    # Mock serial port methods
    mock_close_port = mocker.patch.object(serial.Serial, 'close')

    # Call method under test
    serial_service.stopConnection()

    # Assertions
    assert mock_close_port.call_count == (1 if open_port else 0)


def test_get_ports(mocker: MockerFixture):
    # Mock serial port class method
    mock_list_ports = mocker.patch('serial.tools.list_ports.comports')

    # Call method under test
    SerialService.get_ports()

    # Assertions
    assert mock_list_ports.call_count == 1


@pytest.mark.parametrize('in_waiting', [True, False])
def test_is_waiting(mocker: MockerFixture, in_waiting):
    # Mock state
    mock_in_waiting = mocker.PropertyMock(return_value=in_waiting)
    mocker.patch.object(serial.Serial, 'in_waiting', new_callable=mock_in_waiting)

    # Call method under test
    serial_service = SerialService()
    response = serial_service.waiting()

    # Assertions
    assert response is in_waiting
    mock_in_waiting.assert_called_once()
