import pytest
from celery.app.task import Task
from database.repositories.taskRepository import TaskRepository
from grbl.grblController import GrblController
from pytest_mock.plugin import MockerFixture
import time
from typing import TextIO
from worker import executeTask, WORKER_PAUSE_REQUEST, WORKER_RESUME_REQUEST


def test_execute_tasks(mocker: MockerFixture):
    # Manage internal state
    commands_count = 0

    def increment_commands_count(_):
        nonlocal commands_count
        commands_count += 1

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock Redis methods
    mocker.patch('worker.get_value', return_value='')

    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_task_by_id = mocker.patch.object(TaskRepository, 'get_task_by_id')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL methods
    mock_start_connect = mocker.patch.object(GrblController, 'connect')
    mock_start_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mock_stream_line = mocker.patch.object(
        GrblController,
        'sendCommand',
        side_effect=increment_commands_count
    )
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')
    mock_get_grbl_buffer_fill = mocker.patch.object(
        GrblController,
        'getBufferFill',
        return_value=0
    )
    mocker.patch.object(
        GrblController,
        'getCommandsCount',
        side_effect=get_commands_count
    )
    mocker.patch.object(GrblController, 'alarm', return_value=False)
    mocker.patch.object(GrblController, 'failed', return_value=False)

    # Mock FS methods
    mocker.patch('worker.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocked_update_state = mocker.patch.object(Task, 'update_state')

    # Call method under test
    response = executeTask(
        task_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert response is True
    assert mock_start_connect.call_count == 1
    assert mock_get_task_by_id.call_count == 1
    assert mock_get_grbl_buffer_fill.call_count == 4
    assert mock_stream_line.call_count == 3
    mocked_update_state.assert_called()
    assert mock_update_task_status.call_count == 2
    assert mock_start_disconnect.call_count == 1


def test_no_tasks_to_execute(mocker: MockerFixture):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_task_by_id = mocker.patch.object(
        TaskRepository,
        'get_task_by_id',
        return_value=None
    )
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, 'connect')
    mock_stream_line = mocker.patch.object(GrblController, 'sendCommand')

    # Call method under test
    with pytest.raises(Exception) as error:
        executeTask(
            task_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )

    # Assertions
    assert str(error.value) == 'There are no pending tasks to process'
    assert mock_get_task_by_id.call_count == 1
    assert mock_start_connection.call_count == 0
    assert mock_stream_line.call_count == 0
    assert mock_update_task_status.call_count == 0


def test_task_in_progress_exception(mocker: MockerFixture):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=True)

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask(
            task_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )
    assert str(error.value) == 'There is a task currently in progress, please wait until finished'


def test_task_missing_arguments():
    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask()
    assert str(error.value) == (
        "executeTask() missing 4 required positional arguments: "
        "'task_id', 'base_path', 'serial_port', and 'serial_baudrate'"
    )


def test_execute_tasks_file_error(mocker: MockerFixture):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_task_by_id = mocker.patch.object(TaskRepository, 'get_task_by_id')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL methods
    mock_start_connect = mocker.patch.object(GrblController, 'connect')
    mock_start_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')

    # Mock FS methods
    mocker.patch('worker.getFilePath')
    mocker.patch(
        'builtins.open',
        # The 'logging' module uses the 'open' method internally
        side_effect=[TextIO(), TextIO(), Exception('mocked-error')]
    )

    # Call method under test
    with pytest.raises(Exception):
        executeTask(
            task_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )

    # Assertions
    assert mock_start_connect.call_count == 1
    assert mock_get_task_by_id.call_count == 1
    assert mock_start_disconnect.call_count == 1
    assert mock_update_task_status.call_count == 1


def test_execute_tasks_waits_for_buffer(mocker: MockerFixture):
    # Manage internal state
    commands_count = 0

    def increment_commands_count(command):
        nonlocal commands_count
        commands_count += 1

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock Redis methods
    mocker.patch('worker.get_value', return_value='')

    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mocker.patch.object(TaskRepository, 'get_task_by_id')
    mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL methods
    mocker.patch.object(GrblController, 'connect')
    mocker.patch.object(GrblController, 'disconnect')
    mock_stream_line = mocker.patch.object(
        GrblController,
        'sendCommand',
        side_effect=increment_commands_count
    )
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')
    mock_get_grbl_buffer_fill = mocker.patch.object(
        GrblController,
        'getBufferFill',
        side_effect=[100, 100, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
    )
    mocker.patch.object(
        GrblController,
        'getCommandsCount',
        side_effect=get_commands_count
    )
    mocker.patch.object(GrblController, 'alarm', return_value=False)
    mocker.patch.object(GrblController, 'failed', return_value=False)

    # Mock FS methods
    mocker.patch('worker.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocker.patch.object(Task, 'update_state')

    # Call method under test
    executeTask(
        task_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert mock_get_grbl_buffer_fill.call_count == 6
    assert mock_stream_line.call_count == 3


@pytest.mark.parametrize(
    'is_alarm', [False, True]
)
def test_execute_tasks_grbl_error(mocker: MockerFixture, is_alarm):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mocker.patch.object(TaskRepository, 'get_task_by_id')
    mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL error methods
    mocker.patch.object(GrblController, 'failed', return_value=True)
    mocker.patch.object(GrblController, 'alarm', return_value=is_alarm)
    # Mock GRBL state
    mock_error_line = mocker.PropertyMock(return_value='$H')
    mocker.patch.object(GrblController, 'error_line', new_callable=mock_error_line)
    mock_error_data = mocker.PropertyMock(
        return_value={
            'code': 6,
            'message': 'Homing fail',
            'description': 'Homing fail. The active homing cycle was reset.'
        }
    )
    mocker.patch.object(GrblController, 'error_data', new_callable=mock_error_data)

    # Mock other GRBL methods
    mocker.patch.object(GrblController, 'connect')
    mock_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(GrblController, 'sendCommand')
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')
    mocker.patch.object(GrblController, 'getBufferFill', return_value=0)
    mocker.patch.object(GrblController, 'getCommandsCount', return_value=0)

    # Mock FS methods
    mocker.patch('worker.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocker.patch.object(Task, 'update_state')

    # Call method under test
    with pytest.raises(Exception) as error:
        executeTask(
            task_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )

    # Assertions
    expected = 'An alarm was triggered' if is_alarm else 'There was an error'
    assert mock_disconnect.call_count == 1
    assert expected in str(error.value)


def test_execute_tasks_pause(mocker: MockerFixture):
    # Manage internal state
    commands_count = 0

    def increment_commands_count(command):
        nonlocal commands_count
        commands_count += 1

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock Redis methods
    mock_get_store_value = mocker.patch(
        'worker.get_value',
        side_effect=[WORKER_PAUSE_REQUEST, '', '', '', WORKER_RESUME_REQUEST, '', '', '', '']
    )
    mock_set_store_value = mocker.patch('worker.set_value')
    mock_delete_store_value = mocker.patch('worker.delete_value')

    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mocker.patch.object(TaskRepository, 'get_task_by_id')
    mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL methods
    mocker.patch.object(GrblController, 'connect')
    mocker.patch.object(GrblController, 'disconnect')
    mock_stream_line = mocker.patch.object(
        GrblController,
        'sendCommand',
        side_effect=increment_commands_count
    )
    mocker.patch.object(GrblController, 'getStatusReport')
    mocker.patch.object(GrblController, 'getGcodeParserState')
    mocker.patch.object(GrblController, 'getBufferFill', return_value=0)
    mocker.patch.object(
        GrblController,
        'getCommandsCount',
        side_effect=get_commands_count
    )
    mocker.patch.object(GrblController, 'alarm', return_value=False)
    mocker.patch.object(GrblController, 'failed', return_value=False)

    # Mock FS methods
    mocker.patch('worker.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocker.patch.object(Task, 'update_state')

    # Mock additional methods
    mocker.patch.object(time, 'sleep')

    # Call method under test
    executeTask(
        task_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert mock_get_store_value.call_count == 8
    assert mock_set_store_value.call_count == 1
    assert mock_delete_store_value.call_count == 3
    assert mock_stream_line.call_count == 3
