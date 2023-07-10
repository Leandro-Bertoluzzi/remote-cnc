from sqlalchemy.exc import SQLAlchemyError
from database.base import Session
from database.models.tool import Tool

def createTool(name, description):
    # Create a new session
    session = Session()

    # Create the tool
    newTool = Tool(name, description)

    # Persist data in DB
    session.add(newTool)

    # Commit changes in DB
    try:
        session.commit()
        print('The tool was successfully created!')
    except SQLAlchemyError as e:
        raise Exception(f'Error creating the tool in the DB: {e}')

    # Close session
    session.close()

    return

def getAllTools():
    # Create a new session
    session = Session()

    # Get data from DB
    tools = []
    try:
        tools = session.query(Tool).all()
    except SQLAlchemyError as e:
        raise Exception(f'Error retrieving tools from the DB: {e}')

    # Close session
    session.close()

    return tools

def updateTool(id, name, description):
    # Create a new session
    session = Session()

    # Get tool from DB
    try:
        tool = session.query(Tool).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for tool in the DB: {e}')

    if not tool:
        raise Exception(f'Tool with ID {id} was not found')

    # Update the tool's info
    tool.name = name
    tool.description = description

    # Commit changes in DB
    try:
        session.commit()
        print('The tool was successfully updated!')
    except SQLAlchemyError as e:
        raise Exception(f'Error updating the tool in the DB: {e}')

    # Close session
    session.close()

def removeTool(id):
    # Create a new session
    session = Session()

    # Get tool from DB
    try:
        tool = session.query(Tool).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for tool in the DB: {e}')

    if not tool:
        raise Exception(f'Tool with ID {id} was not found')

    # Remove the tool
    session.delete(tool)

    # Commit changes in DB
    try:
        session.commit()
        print('The tool was successfully removed!')
    except SQLAlchemyError as e:
        raise Exception(f'Error removing the tool from the DB: {e}')

    # Close session
    session.close()
