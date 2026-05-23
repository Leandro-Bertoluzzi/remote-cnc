"""Service layer for Tool domain operations."""

from core.domain.entities import Tool

from desktop.services import get_db_session
from desktop.services.dependencies import get_tool_repository


class ToolService:
    """Encapsulates all tool-related database operations."""

    @classmethod
    def get_all_tools(cls) -> list[Tool]:
        with get_db_session() as session:
            repository = get_tool_repository(session)
            return repository.get_all_tools()

    @classmethod
    def get_tool_by_id(cls, tool_id: int) -> Tool | None:
        """Returns the tool or None if not found or DB is unavailable."""
        with get_db_session() as session:
            repository = get_tool_repository(session)
            return repository.get_tool_by_id(tool_id)

    @classmethod
    def create_tool(cls, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = get_tool_repository(session)
            repository.create_tool(name, description)

    @classmethod
    def update_tool(cls, tool_id: int, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = get_tool_repository(session)
            repository.update_tool(tool_id, name, description)

    @classmethod
    def remove_tool(cls, tool_id: int) -> None:
        with get_db_session() as session:
            repository = get_tool_repository(session)
            repository.remove_tool(tool_id)
