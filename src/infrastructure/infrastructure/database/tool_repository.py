from __future__ import annotations

from core.domain.exceptions import EntityNotFoundError, PersistenceError
from core.ports.db_session import DbSession
from core.ports.tool_repository import IToolRepository
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.database.mappers import to_tool_domain
from infrastructure.database.models import Tool


class ToolRepository(IToolRepository):
    def __init__(self, _session: DbSession):
        self.session = _session

    def create_tool(self, name: str, description: str):
        try:
            new_tool = Tool(name=name, description=description)
            self.session.add(new_tool)
            self.session.commit()
            self.session.refresh(new_tool)
            return to_tool_domain(new_tool)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error creating the tool in the DB: {e}") from e

    def get_tool_by_id(self, id: int):
        try:
            tool = self.session.get(Tool, id)
        except SQLAlchemyError as e:
            raise PersistenceError(f"Error retrieving the tool with ID {id}: {e}") from e

        if not tool:
            raise EntityNotFoundError(f"Tool with ID {id} was not found")
        return to_tool_domain(tool)

    def get_all_tools(self):
        try:
            tools = self.session.scalars(select(Tool)).all()
            return [to_tool_domain(tool) for tool in tools]
        except SQLAlchemyError as e:
            raise PersistenceError(f"Error retrieving tools from the DB: {e}") from e

    def update_tool(self, id: int, name: str, description: str):
        try:
            tool = self.session.get(Tool, id)
            if not tool:
                raise EntityNotFoundError(f"Tool with ID {id} was not found")

            tool.name = name
            tool.description = description
            self.session.commit()
            self.session.refresh(tool)
            return to_tool_domain(tool)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error updating the tool in the DB: {e}") from e

    def remove_tool(self, id: int):
        try:
            tool = self.session.get(Tool, id)
            if not tool:
                raise EntityNotFoundError(f"Tool with ID {id} was not found")

            self.session.delete(tool)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error removing the tool from the DB: {e}") from e
