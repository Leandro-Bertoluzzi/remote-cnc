import pytest
from celery.app.task import Task
from grbl.grblController import GrblController
from worker.tasks import executeTask

def test_execute_tasks(mocker):
    # Mock DB methods
    mocker.patch('worker.tasks.are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch('worker.tasks.get_next_task')
    mock_update_task_status = mocker.patch('worker.tasks.update_task_status')

    queued_tasks = 2
    mock_ask_for_pending_tasks = mocker.patch('worker.tasks.are_there_pending_tasks', side_effect=[True, True, False])

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, 'connect')
    mock_stream_line = mocker.patch.object(GrblController, 'streamLine')
    mock_query_status_report = mocker.patch.object(GrblController, 'queryStatusReport')
    mock_query_parser_state = mocker.patch.object(GrblController, 'queryGcodeParserState')

    # Mock FS methods
    mocked_file_data = mocker.mock_open(read_data='G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60')
    mocker.patch('builtins.open', mocked_file_data)

    # Mock Celery class methods
    mocked_update_state = mocker.patch.object(Task, 'update_state')

    # Call method under test
    response = executeTask()

    # Assertions
    assert response
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
    mocker.patch('worker.tasks.are_there_tasks_in_progress', return_value=False)
    mock_get_next_task = mocker.patch('worker.tasks.get_next_task')
    mock_update_task_status = mocker.patch('worker.tasks.update_task_status')
    mock_ask_for_pending_tasks = mocker.patch('worker.tasks.are_there_pending_tasks', return_value=False)

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, 'connect')
    mock_stream_line = mocker.patch.object(GrblController, 'streamLine')

    # Call method under test
    response = executeTask()

    # Assertions
    assert response
    assert mock_start_connection.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == 1
    assert mock_get_next_task.call_count == 0
    assert mock_stream_line.call_count == 0
    assert mock_update_task_status.call_count == 0

def test_task_in_progress_exception(mocker):
    # Mock DB methods
    mocker.patch('worker.tasks.are_there_tasks_in_progress', return_value=True)

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask()
    assert str(error.value) == 'There is a task currently in progress, please wait until finished'
