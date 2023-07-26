import pytest
from utils.serial import SerialService
from worker.tasks import executeTask

def test_execute_tasks(mocker):
    # Mock DB methods
    mocker.patch('worker.tasks.areThereTasksInProgress', return_value=False)
    mock_get_next_task = mocker.patch('worker.tasks.getNextTask')
    mock_update_task_status = mocker.patch('worker.tasks.updateTaskStatus')

    queued_tasks = 2
    mock_ask_for_pending_tasks = mocker.patch('worker.tasks.areTherePendingTasks', side_effect=[True, True, False])

    # Mock serial port methods
    mock_start_connection = mocker.patch.object(SerialService, 'startConnection')
    mock_send_line = mocker.patch.object(SerialService, 'streamLine')

    # Mock FS methods
    mocked_file_data = mocker.mock_open(read_data="G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60")
    mocker.patch("builtins.open", mocked_file_data)

    # Call method under test
    response = executeTask()

    # Assertions
    assert response
    assert mock_start_connection.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == queued_tasks + 1
    assert mock_get_next_task.call_count == queued_tasks
    assert mock_send_line.call_count == 3 * queued_tasks
    assert mock_update_task_status.call_count == queued_tasks

def test_no_tasks_to_execute(mocker):
    # Mock DB methods
    mocker.patch('worker.tasks.areThereTasksInProgress', return_value=False)
    mock_get_next_task = mocker.patch('worker.tasks.getNextTask')
    mock_update_task_status = mocker.patch('worker.tasks.updateTaskStatus')
    mock_ask_for_pending_tasks = mocker.patch('worker.tasks.areTherePendingTasks', return_value=False)

    # Mock serial port methods
    mock_start_connection = mocker.patch.object(SerialService, 'startConnection')
    mock_send_line = mocker.patch.object(SerialService, 'streamLine')

    # Call method under test
    response = executeTask()

    # Assertions
    assert response
    assert mock_start_connection.call_count == 1
    assert mock_ask_for_pending_tasks.call_count == 1
    assert mock_get_next_task.call_count == 0
    assert mock_send_line.call_count == 0
    assert mock_update_task_status.call_count == 0

def test_task_in_progress_exception(mocker):
    # Mock DB methods
    mocker.patch('worker.tasks.areThereTasksInProgress', return_value=True)

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask()
    assert str(error.value) == 'There is a task currently in progress, please wait until finished'
