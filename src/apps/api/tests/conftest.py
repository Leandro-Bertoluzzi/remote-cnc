from collections.abc import Generator
from dataclasses import replace
from datetime import datetime
from importlib import import_module
from unittest.mock import MagicMock, patch

import pytest
from core.domain.entities import File, Material, Task, Tool, User
from core.domain.task import TaskStatus
from core.ports.file_storage import IFileStorage
from core.ports.logger import ILogger
from fastapi.testclient import TestClient
from manager.adapters.api.context import AppContext
from manager.application.device_service import DeviceService
from manager.application.file_service import FileService
from manager.application.log_service import LogService
from manager.application.material_service import MaterialService
from manager.application.task_service import TaskService
from manager.application.tool_service import ToolService
from manager.application.user_service import UserService

from apps.api.tests.fakes import FakeGatewayClient, FakeLogStorage, FakeWorkerClient


@pytest.fixture(autouse=True)
def token_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "core.utilities.security.TOKEN_SECRET", "api-tests-secret-key-32-bytes-long"
    )


@pytest.fixture(scope="session")
def api_app():
    with patch("infrastructure.logging.logger_factory.setup_stream_logger"):
        return import_module("apps.api.main").app


@pytest.fixture
def test_user() -> User:
    return User(
        id=1,
        name="User",
        email="user@test.com",
        password="password",
        role="user",
    )


@pytest.fixture
def test_admin() -> User:
    return User(
        id=2,
        name="Admin",
        email="admin@test.com",
        password="password",
        role="admin",
    )


@pytest.fixture
def test_tool() -> Tool:
    return Tool(id=1, name="Tool 1", description="A useful tool", added_at=datetime(2000, 1, 1))


@pytest.fixture
def test_material() -> Material:
    return Material(
        id=1, name="Material 1", description="A useful material", added_at=datetime(2000, 1, 1)
    )


@pytest.fixture
def test_file(test_user: User) -> File:
    return File(
        id=1,
        user_id=1,
        file_name="file_1.gcode",
        file_hash="hash-1",
        created_at=datetime(2000, 1, 1),
        user=test_user,
    )


@pytest.fixture
def test_other_file(test_user: User) -> File:
    return File(
        id=2,
        user_id=1,
        file_name="file_2.gcode",
        file_hash="hash-2",
        created_at=datetime(2000, 1, 1),
        user=test_user,
    )


@pytest.fixture
def test_task(test_user: User, test_file: File, test_tool: Tool, test_material: Material) -> Task:
    return Task(
        id=1,
        user_id=1,
        file_id=1,
        tool_id=1,
        material_id=1,
        name="Task 1",
        note="A note",
        status=TaskStatus.PENDING_APPROVAL.value,
        created_at=datetime(2000, 1, 1),
        file=test_file,
        tool=test_tool,
        material=test_material,
        user=test_user,
    )


@pytest.fixture
def log_storage(tmp_path) -> FakeLogStorage:
    return FakeLogStorage(tmp_path / "logs")


@pytest.fixture
def app_context(
    test_user: User,
    test_admin: User,
    log_storage: FakeLogStorage,
) -> AppContext:
    users = {test_user.id: test_user, test_admin.id: test_admin}
    user_service = MagicMock(spec=UserService)

    def get_user_by_id(user_id: int) -> User:
        user = users.get(user_id)
        if user is None:
            raise Exception(f"User with ID {user_id} was not found")
        return user

    user_service.get_user_by_id.side_effect = get_user_by_id
    user_service.get_all_users.return_value = []

    tool_service = MagicMock(spec=ToolService)
    tool_service.get_all_tools.return_value = []
    return AppContext(
        gateway=FakeGatewayClient(),
        worker=FakeWorkerClient(),
        file_storage=MagicMock(spec=IFileStorage),
        session_factory=MagicMock(),
        logger=MagicMock(spec=ILogger),
        device_service=MagicMock(spec=DeviceService),
        file_service=MagicMock(spec=FileService),
        log_service=LogService(log_storage),
        material_service=MagicMock(spec=MaterialService),
        task_service=MagicMock(spec=TaskService),
        tool_service=tool_service,
        user_service=user_service,
    )


@pytest.fixture
def client(api_app, app_context: AppContext) -> Generator[TestClient, None, None]:
    api_app.state.context = app_context
    yield TestClient(api_app, raise_server_exceptions=False)
    del api_app.state.context


@pytest.fixture
def user_headers(test_user: User) -> dict[str, str]:
    from core.utilities.security import generate_token

    return {"Authorization": f"Bearer {generate_token(test_user.id)}"}


@pytest.fixture
def admin_headers(test_admin: User) -> dict[str, str]:
    from core.utilities.security import generate_token

    return {"Authorization": f"Bearer {generate_token(test_admin.id)}"}
