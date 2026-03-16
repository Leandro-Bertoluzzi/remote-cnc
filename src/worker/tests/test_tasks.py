import time
from unittest.mock import MagicMock

import pytest
from celery.app.task import Task
from core.database.models import TaskStatus
from core.database.repositories.taskRepository import TaskRepository
from core.utilities.gcode.gcodeFileSender import FinishedFile, GcodeFileSender
from core.utilities.grbl.grblController import GrblController, GrblStatus
from core.utilities.worker.workerStatusManager import WorkerStatusManager
from pytest_mock.plugin import MockerFixture
from worker.tasks.cnc import executeTask


def _mock_infrastructure(mocker: MockerFixture) -> None:
    """Mock Redis and logger to prevent external connections."""
    mocker.patch("worker.tasks.cnc.RedisPubSubManagerSync")
    mocker.patch("core.utilities.grbl.grblMonitor.RedisPubSubManagerSync")
    mocker.patch("worker.tasks.cnc.setup_task_logger", return_value=MagicMock())
    mocker.patch("worker.tasks.cnc.get_task_logger", return_value=MagicMock())
    mocker.patch("worker.tasks.cnc.SessionLocal", return_value=MagicMock())


def _create_mock_task(task_id: int = 1) -> MagicMock:
    """Create a properly configured mock task."""
    mock_task = MagicMock()
    mock_task.status = TaskStatus.APPROVED.value
    mock_task.id = task_id
    mock_task.tool_id = 1
    mock_task.file.user_id = 1
    mock_task.file.file_name = "test.gcode"
    return mock_task


def test_execute_tasks(mocker: MockerFixture):
    _mock_infrastructure(mocker)

    # Manage internal state
    commands_count = 0

    def increment_commands_count():
        nonlocal commands_count
        commands_count += 1
        if commands_count == 4:
            raise FinishedFile
        return commands_count

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock WorkerStatusManager methods
    mocker.patch.object(WorkerStatusManager, "process_request", return_value=(False, False))
    mocker.patch.object(WorkerStatusManager, "is_paused", return_value=False)

    # Mock DB methods
    mock_task = _create_mock_task(task_id=2)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mock_get_task_by_id = mocker.patch.object(
        TaskRepository, "get_task_by_id", return_value=mock_task
    )
    mock_update_task_status = mocker.patch.object(TaskRepository, "update_task_status")

    # Mock GRBL methods
    mock_start_connect = mocker.patch.object(GrblController, "connect")
    mock_start_disconnect = mocker.patch.object(GrblController, "disconnect")
    mocker.patch.object(GrblController, "send_command")
    mocker.patch.object(GrblStatus, "get_status_report", return_value={})
    mocker.patch.object(GrblStatus, "get_parser_state", return_value={})
    mocker.patch.object(GrblController, "get_commands_count", side_effect=get_commands_count)
    mocker.patch.object(GrblStatus, "failed", return_value=False)
    mocker.patch.object(GrblStatus, "finished", return_value=False)

    # Mock file sender methods
    mocker.patch.object(GcodeFileSender, "start", return_value=3)
    mock_stream_line = mocker.patch.object(
        GcodeFileSender, "send_line", side_effect=increment_commands_count
    )
    mocker.patch.object(GcodeFileSender, "stop")

    # Mock Celery class methods
    mocked_update_state = mocker.patch.object(Task, "update_state")

    # Call method under test
    executeTask(task_id=2, serial_port="test-port", serial_baudrate=115200)

    # Assertions
    assert mock_start_connect.call_count == 1
    assert mock_get_task_by_id.call_count == 1
    assert mock_stream_line.call_count == 4
    mocked_update_state.assert_called()
    assert mock_update_task_status.call_count == 2
    assert mock_start_disconnect.call_count == 1


def test_no_tasks_to_execute(mocker: MockerFixture):
    _mock_infrastructure(mocker)

    # Mock DB methods
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mock_get_task_by_id = mocker.patch.object(TaskRepository, "get_task_by_id", return_value=None)
    mock_update_task_status = mocker.patch.object(TaskRepository, "update_task_status")

    # Mock GRBL methods
    mock_start_connection = mocker.patch.object(GrblController, "connect")
    # Mock file sender methods
    mock_stream_line = mocker.patch.object(GcodeFileSender, "send_line")

    # Call method under test
    with pytest.raises(Exception) as error:
        executeTask(task_id=1, serial_port="test-port", serial_baudrate=115200)

    # Assertions
    assert str(error.value) == "No se encontró la tarea en la base de datos"
    assert mock_get_task_by_id.call_count == 1
    assert mock_start_connection.call_count == 0
    assert mock_stream_line.call_count == 0
    assert mock_update_task_status.call_count == 0


def test_task_in_progress_exception(mocker: MockerFixture):
    _mock_infrastructure(mocker)

    # Mock DB methods
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=True)

    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask(task_id=1, serial_port="test-port", serial_baudrate=115200)
    assert str(error.value) == "Ya hay una tarea en progreso, por favor espere a que termine"


def test_task_missing_arguments():
    # Call the method under test and assert exception
    with pytest.raises(Exception) as error:
        executeTask()
    assert str(error.value) == (
        "executeTask() missing 3 required positional arguments: "
        "'task_id', 'serial_port', and 'serial_baudrate'"
    )


def test_execute_tasks_file_error(mocker: MockerFixture):
    _mock_infrastructure(mocker)

    # Mock DB methods
    mock_task = _create_mock_task(task_id=1)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mock_get_task_by_id = mocker.patch.object(
        TaskRepository, "get_task_by_id", return_value=mock_task
    )
    mock_update_task_status = mocker.patch.object(TaskRepository, "update_task_status")

    # Mock GRBL methods
    mock_start_connect = mocker.patch.object(GrblController, "connect")
    mock_start_disconnect = mocker.patch.object(GrblController, "disconnect")
    mocker.patch.object(GrblStatus, "get_status_report", return_value={})
    mocker.patch.object(GrblStatus, "get_parser_state", return_value={})

    # Mock file sender methods
    mocker.patch.object(GcodeFileSender, "start", side_effect=Exception("mocked-error"))

    # Call method under test
    with pytest.raises(Exception, match="mocked-error"):
        executeTask(task_id=1, serial_port="test-port", serial_baudrate=115200)

    # Assertions
    assert mock_start_connect.call_count == 1
    assert mock_get_task_by_id.call_count == 1
    # disconnect is called once in the except block, then cnc is set to None
    # so the finally block does NOT call disconnect again
    assert mock_start_disconnect.call_count == 1
    # update_task_status is never called because start() fails before it
    assert mock_update_task_status.call_count == 0


def test_execute_tasks_grbl_error(mocker: MockerFixture):
    _mock_infrastructure(mocker)

    # Mock DB methods
    mock_task = _create_mock_task(task_id=1)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mocker.patch.object(TaskRepository, "update_task_status")

    # Mock GRBL error methods
    mocker.patch.object(GrblStatus, "failed", return_value=True)
    mocker.patch.object(GrblStatus, "get_error_message", return_value="An error message")

    # Mock other GRBL methods
    mocker.patch.object(GrblController, "connect")
    mock_disconnect = mocker.patch.object(GrblController, "disconnect")
    mocker.patch.object(GrblController, "send_command")
    mocker.patch.object(GrblStatus, "get_status_report", return_value={})
    mocker.patch.object(GrblStatus, "get_parser_state", return_value={})
    mocker.patch.object(GrblController, "get_commands_count", return_value=0)

    # Mock file sender methods
    mocker.patch.object(GcodeFileSender, "start", return_value=3)
    mocker.patch.object(GcodeFileSender, "send_line")

    # Mock Celery class methods
    mocker.patch.object(Task, "update_state")

    # Call method under test
    with pytest.raises(Exception) as error:
        executeTask(task_id=1, serial_port="test-port", serial_baudrate=115200)

    # Assertions
    assert mock_disconnect.call_count == 1
    assert str(error.value) == "An error message"


def test_execute_tasks_pause(mocker: MockerFixture):
    _mock_infrastructure(mocker)

    # Manage internal state
    commands_count = 0

    def increment_commands_count():
        nonlocal commands_count
        commands_count += 1
        if commands_count == 4:
            raise FinishedFile
        return commands_count

    def get_commands_count():
        nonlocal commands_count
        return commands_count

    # Mock WorkerStatusManager methods
    mock_process_request = mocker.patch.object(
        WorkerStatusManager,
        "process_request",
        side_effect=[
            (True, False),
            (False, False),
            (False, False),
            (False, False),
            (False, True),
            (False, False),
            (False, False),
            (False, False),
            (False, False),
        ],
    )
    mocker.patch.object(
        WorkerStatusManager,
        "is_paused",
        side_effect=[True, True, True, True, False, False, False, False, False],
    )

    # Mock DB methods
    mock_task = _create_mock_task(task_id=2)
    mocker.patch.object(TaskRepository, "are_there_tasks_in_progress", return_value=False)
    mocker.patch.object(TaskRepository, "get_task_by_id", return_value=mock_task)
    mocker.patch.object(TaskRepository, "update_task_status")

    # Mock GRBL methods
    mocker.patch.object(GrblController, "connect")
    mocker.patch.object(GrblController, "disconnect")
    mocker.patch.object(GrblController, "send_command")
    mocker.patch.object(GrblController, "set_paused")
    mocker.patch.object(GrblStatus, "get_status_report", return_value={})
    mocker.patch.object(GrblStatus, "get_parser_state", return_value={})
    mocker.patch.object(GrblController, "get_commands_count", side_effect=get_commands_count)
    mocker.patch.object(GrblStatus, "failed", return_value=False)
    mocker.patch.object(GrblStatus, "finished", return_value=False)

    # Mock file sender methods
    mocker.patch.object(GcodeFileSender, "start", return_value=3)
    mock_stream_line = mocker.patch.object(
        GcodeFileSender, "send_line", side_effect=increment_commands_count
    )
    mocker.patch.object(GcodeFileSender, "pause")
    mocker.patch.object(GcodeFileSender, "resume")
    mocker.patch.object(GcodeFileSender, "stop")

    # Mock Celery class methods
    mocker.patch.object(Task, "update_state")

    # Mock additional methods
    mocker.patch.object(time, "sleep")

    # Call method under test
    executeTask(task_id=2, serial_port="test-port", serial_baudrate=115200)

    # Assertions
    assert mock_process_request.call_count == 8
    assert mock_stream_line.call_count == 4
