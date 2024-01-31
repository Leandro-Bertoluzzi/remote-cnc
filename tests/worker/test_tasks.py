import pytest
from celery.app.task import Task
from database.repositories.taskRepository import TaskRepository
from grbl.grblController import GrblController
from typing import BinaryIO
from worker.tasks import executeTask


def test_execute_tasks(mocker):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch.object(TaskRepository, 'get_next_task')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')

    queued_tasks = 2
    mock_ask_for_pending_tasks = mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        side_effect=[True, True, False]
    )

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, 'connect')
    mock_stream_line = mocker.patch.object(GrblController, 'streamLine')
    mock_query_status_report = mocker.patch.object(GrblController, 'queryStatusReport')
    mock_query_parser_state = mocker.patch.object(GrblController, 'queryGcodeParserState')

    # Mock FS methods
    mocker.patch('worker.tasks.getFilePath')
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocked_update_state = mocker.patch.object(Task, 'update_state')

    # Call method under test
    response = executeTask(
        admin_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert response is True
    assert mock_start_connection.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == queued_tasks + 1
    assert mock_get_next_task.call_count == queued_tasks
    assert mock_stream_line.call_count == 3 * queued_tasks
    assert mock_query_status_report.call_count == 3 * queued_tasks
    assert mock_query_parser_state.call_count == 3 * queued_tasks
    assert mocked_update_state.call_count == 3 * queued_tasks
    assert mock_update_task_status.call_count == 2 * queued_tasks


def test_no_tasks_to_execute(mocker):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch.object(TaskRepository, 'get_next_task')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')
    mock_ask_for_pending_tasks = mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        return_value=False
    )

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, 'connect')
    mock_stream_line = mocker.patch.object(GrblController, 'streamLine')

    # Call method under test
    response = executeTask(
        admin_id=1,
        base_path='path/to/project',
        serial_port='test-port',
        serial_baudrate=115200
    )

    # Assertions
    assert response is True
    assert mock_start_connection.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == 1
    assert mock_get_next_task.call_count == 0
    assert mock_stream_line.call_count == 0
    assert mock_update_task_status.call_count == 0


def test_task_in_progress_exception(mocker):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=True)

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask(
            admin_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )
    assert str(error.value) == 'There is a task currently in progress, please wait until finished'

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask()
    assert str(error.value) == (
        "executeTask() missing 4 required positional arguments: "
        "'admin_id', 'base_path', 'serial_port', and 'serial_baudrate'"
    )


def test_execute_tasks_file_error(mocker):
    # Mock DB methods
    mocker.patch.object(TaskRepository, 'are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch.object(TaskRepository, 'get_next_task')
    mock_update_task_status = mocker.patch.object(TaskRepository, 'update_task_status')
    mock_ask_for_pending_tasks = mocker.patch.object(
        TaskRepository,
        'are_there_pending_tasks',
        return_value=True
    )

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, 'connect')

    # Mock FS methods
    mocker.patch('worker.tasks.getFilePath')
    mocker.patch(
        'builtins.open',
        # The 'logging' module uses the 'open' method internally
        side_effect=[BinaryIO(), Exception('mocked-error')]
    )

    # Call method under test
    with pytest.raises(Exception):
        executeTask(
            admin_id=1,
            base_path='path/to/project',
            serial_port='test-port',
            serial_baudrate=115200
        )

    # Assertions
    assert mock_start_connection.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == 1
    assert mock_get_next_task.call_count == 1
    assert mock_update_task_status.call_count == 0
