from unittest.mock import MagicMock

from desktop.services.toolService import ToolService
from pytest_mock.plugin import MockerFixture


class TestToolService:
    @staticmethod
    def _mock_db_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = session
        session_ctx.__exit__.return_value = None

        mocker.patch("desktop.services.toolService.get_db_session", return_value=session_ctx)
        repository = MagicMock()
        get_repo = mocker.patch(
            "desktop.services.toolService.get_tool_repository",
            return_value=repository,
        )
        return session, repository, get_repo

    def test_get_all_tools(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        expected = [MagicMock(), MagicMock()]
        repository.get_all_tools.return_value = expected

        result = ToolService.get_all_tools()

        assert result == expected
        get_repo.assert_called_once_with(session)
        repository.get_all_tools.assert_called_once_with()

    def test_create_tool(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        result = ToolService.create_tool("Tool", "desc")

        get_repo.assert_called_once_with(session)
        repository.create_tool.assert_called_once_with("Tool", "desc")
        assert result is None

    def test_remove_tool(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        ToolService.remove_tool(tool_id=9)

        get_repo.assert_called_once_with(session)
        repository.remove_tool.assert_called_once_with(9)
