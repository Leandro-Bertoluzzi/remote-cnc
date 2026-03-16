"""Service layer for Tool domain operations."""

from core.database.models import Tool
from core.database.repositories.toolRepository import ToolRepository

from desktop.services import get_db_session


class ToolService:
    """Encapsulates all tool-related database operations."""

    @classmethod
    def get_all_tools(cls) -> list[Tool]:
        with get_db_session() as session:
            repository = ToolRepository(session)
            return repository.get_all_tools()

    @classmethod
    def get_tool_by_id(cls, tool_id: int) -> Tool | None:
        """Returns the tool or None if not found or DB is unavailable."""
        with get_db_session() as session:
            repository = ToolRepository(session)
            return repository.get_tool_by_id(tool_id)

    @classmethod
    def create_tool(cls, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = ToolRepository(session)
            repository.create_tool(name, description)

    @classmethod
    def update_tool(cls, tool_id: int, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = ToolRepository(session)
            repository.update_tool(tool_id, name, description)

    @classmethod
    def remove_tool(cls, tool_id: int) -> None:
        with get_db_session() as session:
            repository = ToolRepository(session)
            repository.remove_tool(tool_id)
