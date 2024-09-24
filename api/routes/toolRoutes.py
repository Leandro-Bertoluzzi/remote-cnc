from core.database.repositories.toolRepository import ToolRepository
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.general import GenericResponse
from schemas.tools import ToolRequest, ToolResponse

toolRoutes = APIRouter(prefix="/tools", tags=["Tools"])


@toolRoutes.get('')
@toolRoutes.get('/')
@toolRoutes.get('/all')
def get_tools(
    user: GetUserDep,
    db_session: GetDbSession
) -> list[ToolResponse]:
    repository = ToolRepository(db_session)
    tools = repository.get_all_tools()

    return [ToolResponse.from_orm(tool) for tool in tools]


@toolRoutes.get('/{tool_id}', response_model=ToolResponse)
def get_tool_by_id(
    tool_id: int,
    user: GetUserDep,
    db_session: GetDbSession
):
    try:
        repository = ToolRepository(db_session)
        result = repository.get_tool_by_id(tool_id)
        return ToolResponse.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@toolRoutes.post('', response_model=ToolResponse)
@toolRoutes.post('/', response_model=ToolResponse)
def create_new_tool(
    request: ToolRequest,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository(db_session)
        return repository.create_tool(toolName, toolDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@toolRoutes.put('/{tool_id}', response_model=ToolResponse)
def update_existing_tool(
    request: ToolRequest,
    tool_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository(db_session)
        result = repository.update_tool(tool_id, toolName, toolDescription)
        return ToolResponse.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@toolRoutes.delete('/{tool_id}', response_model=GenericResponse)
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

    return {'success': 'La herramienta fue eliminada con éxito'}
