from sqlalchemy.exc import SQLAlchemyError
from ..base import Session
from ..models.tool import Tool


class ToolRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_tool(self, name, description):
        try:
            new_tool = Tool(name=name, description=description)
            self.session.add(new_tool)
            self.session.commit()
            return new_tool
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error creating the tool in the DB: {e}')

    def get_tool_by_id(self, id):
        try:
            tool = self.session.query(Tool).get(id)
            if not tool:
                raise Exception(f'Tool with ID {id} was not found')
            return tool
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving the tool with ID {id}: {e}')

    def get_all_tools(self):
        try:
            tools = self.session.query(Tool).all()
            return tools
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving tools from the DB: {e}')

    def update_tool(self, id, name, description):
        try:
            tool = self.session.query(Tool).get(id)
            if not tool:
                raise Exception(f'Tool with ID {id} was not found')

            tool.name = name
            tool.description = description
            self.session.commit()
            return tool
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error updating the tool in the DB: {e}')

    def remove_tool(self, id):
        try:
            tool = self.session.query(Tool).get(id)
            if not tool:
                raise Exception(f'Tool with ID {id} was not found')

            self.session.delete(tool)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error removing the tool from the DB: {e}')

    def close_session(self):
        self.session.close()
