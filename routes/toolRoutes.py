from authMiddleware import GetAdminDep
from core.database.repositories.toolRepository import ToolRepository
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utilities.utils import serializeList

toolRoutes = APIRouter()


class ToolRequestModel(BaseModel):
    name: str
    description: str


@toolRoutes.get('/tools/')
@toolRoutes.get('/tools/all')
def get_tools(admin: GetAdminDep):
    repository = ToolRepository()
    tools = serializeList(repository.get_all_tools())
    return tools


@toolRoutes.post('/tools/')
def create_tool(request: ToolRequestModel, admin: GetAdminDep):
    # Get data from request body
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository()
        repository.create_tool(toolName, toolDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The tool was successfully created'}


@toolRoutes.put('/tools/{tool_id}')
def update_tool(
    request: ToolRequestModel,
    tool_id: int,
    admin: GetAdminDep
):
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository()
        repository.update_tool(tool_id, toolName, toolDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The tool was successfully updated'}


@toolRoutes.delete('/tools/{tool_id}')
def remove_tool(tool_id: int, admin: GetAdminDep):
    try:
        repository = ToolRepository()
        repository.remove_tool(tool_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The tool was successfully removed'}
