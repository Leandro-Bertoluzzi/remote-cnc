"""Port for tool persistence operations."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.domain.entities import Tool


@runtime_checkable
class IToolRepository(Protocol):
    def create_tool(self, name: str, description: str) -> Tool: ...

    def get_tool_by_id(self, id: int) -> Tool: ...

    def get_all_tools(self) -> list[Tool]: ...

    def update_tool(self, id: int, name: str, description: str) -> Tool: ...

    def remove_tool(self, id: int) -> None: ...
