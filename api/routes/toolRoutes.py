from core.database.repositories.toolRepository import ToolRepository
import datetime
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from pydantic import BaseModel
from services.utilities import serializeList

toolRoutes = APIRouter(prefix="/tools", tags=["Tools"])


class ToolRequestModel(BaseModel):
    name: str
    description: str


class ToolResponseModel(BaseModel):
    id: int
    name: str
    description: str
    added_at: datetime.datetime


@toolRoutes.get('')
@toolRoutes.get('/')
@toolRoutes.get('/all')
def get_tools(
    user: GetUserDep,
    db_session: GetDbSession
) -> list[ToolResponseModel]:
    repository = ToolRepository(db_session)
    tools = serializeList(repository.get_all_tools())
    return tools


@toolRoutes.get('/{tool_id}')
def get_tool_by_id(
    tool_id: int,
    user: GetUserDep,
    db_session: GetDbSession
) -> ToolResponseModel:
    try:
        repository = ToolRepository(db_session)
        tool = repository.get_tool_by_id(tool_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {
        'id': tool.id,
        'name': tool.name,
        'description': tool.description,
        'added_at': tool.added_at
    }


@toolRoutes.post('')
@toolRoutes.post('/')
def create_new_tool(
    request: ToolRequestModel,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> ToolResponseModel:
    # Get data from request body
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository(db_session)
        tool = repository.create_tool(toolName, toolDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return tool


@toolRoutes.put('/{tool_id}')
def update_existing_tool(
    request: ToolRequestModel,
    tool_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository(db_session)
        repository.update_tool(tool_id, toolName, toolDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The tool was successfully updated'}


@toolRoutes.delete('/{tool_id}')
def remove_existing_tool(
    tool_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    try:
        repository = ToolRepository(db_session)
        repository.remove_tool(tool_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The tool was successfully removed'}
