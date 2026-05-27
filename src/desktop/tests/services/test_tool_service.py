from unittest.mock import MagicMock

from desktop.services.toolService import ToolService
from pytest_mock.plugin import MockerFixture


class TestToolService:
    @staticmethod
    def _make_service_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None
        repository = MagicMock()
        mocker.patch(
            "desktop.services.toolService.get_tool_repository",
            return_value=repository,
        )
        service = ToolService(session_factory=session_factory)
        return service, session, repository

    def test_get_all_tools(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)
        expected = [MagicMock(), MagicMock()]
        repository.get_all_tools.return_value = expected

        result = service.get_all_tools()

        assert result == expected
        repository.get_all_tools.assert_called_once_with()

    def test_create_tool(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)

        result = service.create_tool("Tool", "desc")

        repository.create_tool.assert_called_once_with("Tool", "desc")
        assert result is None

    def test_remove_tool(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)

        service.remove_tool(tool_id=9)

        repository.remove_tool.assert_called_once_with(9)
