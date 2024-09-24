from core.database.repositories.toolRepository import ToolRepository
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.general import GenericResponseModel
from schemas.tools import ToolRequestModel, ToolResponseModel

toolRoutes = APIRouter(prefix="/tools", tags=["Tools"])


@toolRoutes.get('')
@toolRoutes.get('/')
@toolRoutes.get('/all')
def get_tools(
    user: GetUserDep,
    db_session: GetDbSession
) -> list[ToolResponseModel]:
    repository = ToolRepository(db_session)
    tools = repository.get_all_tools()

    return [ToolResponseModel.from_orm(tool) for tool in tools]


@toolRoutes.get('/{tool_id}')
def get_tool_by_id(
    tool_id: int,
    user: GetUserDep,
    db_session: GetDbSession
) -> ToolResponseModel:
    try:
        repository = ToolRepository(db_session)
        result = repository.get_tool_by_id(tool_id)
        return ToolResponseModel.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@toolRoutes.post('')
@toolRoutes.post('/')
def create_new_tool(
    request: ToolRequestModel,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> ToolResponseModel:
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository(db_session)
        return repository.create_tool(toolName, toolDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@toolRoutes.put('/{tool_id}')
def update_existing_tool(
    request: ToolRequestModel,
    tool_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> ToolResponseModel:
    toolName = request.name
    toolDescription = request.description

    try:
        repository = ToolRepository(db_session)
        result = repository.update_tool(tool_id, toolName, toolDescription)
        return ToolResponseModel.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@toolRoutes.delete('/{tool_id}')
def remove_existing_tool(
    tool_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> GenericResponseModel:
    try:
        repository = ToolRepository(db_session)
        repository.remove_tool(tool_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'La herramienta fue eliminada con éxito'}
