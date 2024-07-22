from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from ..base import Session
from ..exceptions import DatabaseError, EntityNotFoundError
from ..models import Tool


class ToolRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_tool(self, name: str, description: str):
        try:
            new_tool = Tool(name=name, description=description)
            self.session.add(new_tool)
            self.session.commit()
            return new_tool
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error creating the tool in the DB: {e}')

    def get_tool_by_id(self, id: int):
        try:
            tool = self.session.get(Tool, id)
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error retrieving the tool with ID {id}: {e}')

        if not tool:
            raise EntityNotFoundError(f'Tool with ID {id} was not found')
        return tool

    def get_all_tools(self):
        try:
            tools = self.session.execute(
                select(Tool)
            ).scalars().all()
            return tools
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error retrieving tools from the DB: {e}')

    def update_tool(self, id: int, name: str, description: str):
        try:
            tool = self.session.get(Tool, id)
            if not tool:
                raise EntityNotFoundError(f'Tool with ID {id} was not found')

            tool.name = name
            tool.description = description
            self.session.commit()
            return tool
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error updating the tool in the DB: {e}')

    def remove_tool(self, id: int):
        try:
            tool = self.session.get(Tool, id)
            if not tool:
                raise EntityNotFoundError(f'Tool with ID {id} was not found')

            self.session.delete(tool)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error removing the tool from the DB: {e}')

    def close_session(self):
        self.session.close()
