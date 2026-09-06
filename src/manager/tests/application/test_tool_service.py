from unittest.mock import MagicMock

from manager.application.tool_service import ToolService


class TestToolService:
    @staticmethod
    def _make_service_and_repo():
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None
        repository = MagicMock()
        service = ToolService(
            session_factory=session_factory,
            tool_repo_factory=MagicMock(return_value=repository),
        )
        return service, repository

    def test_get_all_tools(self):
        service, repository = self._make_service_and_repo()
        expected = [MagicMock(), MagicMock()]
        repository.get_all_tools.return_value = expected

        result = service.get_all_tools()

        assert result == expected
        repository.get_all_tools.assert_called_once_with()

    def test_get_tool_by_id(self):
        service, repository = self._make_service_and_repo()
        expected = MagicMock()
        repository.get_tool_by_id.return_value = expected

        result = service.get_tool_by_id(5)

        assert result == expected
        repository.get_tool_by_id.assert_called_once_with(5)

    def test_get_tool_by_id_invalid(self):
        service, repository = self._make_service_and_repo()

        result = service.get_tool_by_id(0)

        assert result is None
        repository.get_tool_by_id.assert_not_called()

    def test_create_tool(self):
        service, repository = self._make_service_and_repo()

        result = service.create_tool("Tool", "desc")

        repository.create_tool.assert_called_once_with("Tool", "desc")
        assert result is None

    def test_update_tool(self):
        service, repository = self._make_service_and_repo()

        service.update_tool(4, "Updated Tool", "new desc")

        repository.update_tool.assert_called_once_with(4, "Updated Tool", "new desc")

    def test_remove_tool(self):
        service, repository = self._make_service_and_repo()

        service.remove_tool(tool_id=9)

        repository.remove_tool.assert_called_once_with(9)
