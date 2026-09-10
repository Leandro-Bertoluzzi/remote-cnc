"""Application service for Tool domain operations."""

from collections.abc import Callable

from core.domain.entities import Tool
from core.ports.db_session import DbSession, SessionFactory
from core.ports.tool_repository import IToolRepository


class ToolService:
    """Encapsulates all tool-related database operations."""

    def __init__(
        self,
        session_factory: SessionFactory,
        tool_repo_factory: Callable[[DbSession], IToolRepository],
    ):
        self._session_factory = session_factory
        self._tool_repo_factory = tool_repo_factory

    def get_all_tools(self) -> list[Tool]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._tool_repo_factory(session)
            return repository.get_all_tools()

    def get_tool_by_id(self, tool_id: int) -> Tool | None:
        """Returns the tool or None if not found or DB is unavailable."""
        if tool_id == 0:
            return None  # ID 0 is reserved for "no tool"
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._tool_repo_factory(session)
            return repository.get_tool_by_id(tool_id)

    def create_tool(self, name: str, description: str) -> Tool:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._tool_repo_factory(session)
            return repository.create_tool(name, description)

    def update_tool(self, tool_id: int, name: str, description: str) -> Tool:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._tool_repo_factory(session)
            return repository.update_tool(tool_id, name, description)

    def remove_tool(self, tool_id: int) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._tool_repo_factory(session)
            repository.remove_tool(tool_id)
