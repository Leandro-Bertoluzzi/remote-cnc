import pytest
from celery.app.task import Task
from worker.tasks.cnc import executeTask
from database.repositories.taskRepository import TaskRepository
from utilities.gcode.gcodeFileSender import GcodeFileSender, FinishedFile
from utilities.grbl.grblController import GrblController, GrblStatus
from utilities.worker.workerStatusManager import WorkerStatusManager
from pytest_mock.plugin import MockerFixture
import time


def test_execute_tasks(mocker: MockerFixture):
    # Manage internal state
    commands_count = 0

    def increment_commands_count():
        nonlocal commands_count
        commands_count += 1
        if commands_count == 4:
            raise FinishedFile

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock WorkerStatusManager methods
    mocker.patch.object(
        WorkerStatusManager,
        'process_request',
        return_value=(False, False)
    )
    mocker.patch.object(WorkerStatusManager, 'is_paused', return_value=False)

    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_task_by_id = mocker.patch.object(TaskRepository, 'get_task_by_id')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL methods
    mock_start_connect = mocker.patch.object(GrblController, 'connect')
    mock_start_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(GrblStatus, 'get_status_report')
    mocker.patch.object(GrblStatus, 'get_parser_state')
    mocker.patch.object(
        GrblController,
        'getCommandsCount',
        side_effect=get_commands_count
    )
    mocker.patch.object(GrblStatus, 'failed', return_value=False)
    mocker.patch.object(GrblStatus, 'finished', return_value=False)

    # Mock file sender methods
    mocker.patch.object(GcodeFileSender, 'start', return_value=3)
    mock_stream_line = mocker.patch.object(
        GcodeFileSender,
        'send_line',
        side_effect=increment_commands_count
    )

    # Mock Celery class methods
    mocked_update_state = mocker.patch.object(Task, 'update_state')

    # Call method under test
    response = executeTask(
        task_id=2,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert response is True
    assert mock_start_connect.call_count == 1
    assert mock_get_task_by_id.call_count == 1
    assert mock_stream_line.call_count == 4
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
    # Mock file sender methods
    mock_stream_line = mocker.patch.object(GcodeFileSender, 'send_line')

    # Call method under test
    with pytest.raises(Exception) as error:
        executeTask(
            task_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )

    # Assertions
    assert str(error.value) == 'No se encontró la tarea en la base de datos'
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
    assert str(error.value) == 'Ya hay una tarea en progreso, por favor espere a que termine'


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
    mocker.patch.object(GrblStatus, 'get_status_report')
    mocker.patch.object(GrblStatus, 'get_parser_state')

    # Mock FS methods
    mocker.patch('tasks.getFilePath')

    # Mock file sender methods
    mocker.patch.object(
        GcodeFileSender,
        'start',
        side_effect=Exception('mocked-error')
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


def test_execute_tasks_grbl_error(mocker: MockerFixture):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mocker.patch.object(TaskRepository, 'get_task_by_id')
    mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL error methods
    mocker.patch.object(GrblStatus, 'failed', return_value=True)
    mocker.patch.object(GrblStatus, 'get_error_message', return_value='An error message')

    # Mock other GRBL methods
    mocker.patch.object(GrblController, 'connect')
    mock_disconnect = mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(GrblStatus, 'get_status_report')
    mocker.patch.object(GrblStatus, 'get_parser_state')
    mocker.patch.object(GrblController, 'getCommandsCount', return_value=0)

    # Mock file sender methods
    mocker.patch.object(GcodeFileSender, 'start', return_value=3)
    mocker.patch.object(GcodeFileSender, 'send_line')

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
    assert mock_disconnect.call_count == 1
    assert str(error.value) == 'An error message'


def test_execute_tasks_pause(mocker: MockerFixture):
    # Manage internal state
    commands_count = 0

    def increment_commands_count():
        nonlocal commands_count
        commands_count += 1
        if commands_count == 4:
            raise FinishedFile

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock WorkerStatusManager methods
    mock_process_request = mocker.patch.object(
        WorkerStatusManager,
        'process_request',
        side_effect=[
            (True, False),
            (False, False),
            (False, False),
            (False, False),
            (False, True),
            (False, False),
            (False, False),
            (False, False),
            (False, False)
        ]
    )
    mocker.patch.object(
        WorkerStatusManager,
        'is_paused',
        side_effect=[
            True,
            True,
            True,
            True,
            False,
            False,
            False,
            False,
            False
        ]
    )

    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mocker.patch.object(TaskRepository, 'get_task_by_id')
    mocker.patch.object(TaskRepository, 'update_task_status')

    # Mock GRBL methods
    mocker.patch.object(GrblController, 'connect')
    mocker.patch.object(GrblController, 'disconnect')
    mocker.patch.object(GrblStatus, 'get_status_report')
    mocker.patch.object(GrblStatus, 'get_parser_state')
    mocker.patch.object(
        GrblController,
        'getCommandsCount',
        side_effect=get_commands_count
    )
    mocker.patch.object(GrblStatus, 'failed', return_value=False)
    mocker.patch.object(GrblStatus, 'finished', return_value=False)

    # Mock file sender methods
    mocker.patch.object(GcodeFileSender, 'start', return_value=3)
    mock_stream_line = mocker.patch.object(
        GcodeFileSender,
        'send_line',
        side_effect=increment_commands_count
    )
    mocker.patch.object(GcodeFileSender, 'pause')
    mocker.patch.object(GcodeFileSender, 'resume')

    # Mock Celery class methods
    mocker.patch.object(Task, 'update_state')

    # Mock additional methods
    mocker.patch.object(time, 'sleep')

    # Call method under test
    executeTask(
        task_id=2,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert mock_process_request.call_count == 8
    assert mock_stream_line.call_count == 4
