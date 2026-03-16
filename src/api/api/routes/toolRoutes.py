from core.database.repositories.toolRepository import ToolRepository
from core.schemas.general import GenericResponse
from core.schemas.tools import ToolRequest, ToolResponse
from fastapi import APIRouter

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.dbMiddleware import GetDbSession

toolRoutes = APIRouter(prefix="/tools", tags=["Tools"])


@toolRoutes.get("")
@toolRoutes.get("/")
@toolRoutes.get("/all")
def get_tools(user: GetUserDep, db_session: GetDbSession) -> list[ToolResponse]:
    repository = ToolRepository(db_session)
    tools = repository.get_all_tools()

    return [ToolResponse.model_validate(tool) for tool in tools]


@toolRoutes.get("/{tool_id}", response_model=ToolResponse)
def get_tool_by_id(tool_id: int, user: GetUserDep, db_session: GetDbSession):
    repository = ToolRepository(db_session)
    result = repository.get_tool_by_id(tool_id)
    return ToolResponse.model_validate(result)


@toolRoutes.post("", response_model=ToolResponse)
@toolRoutes.post("/", response_model=ToolResponse)
def create_new_tool(request: ToolRequest, admin: GetAdminDep, db_session: GetDbSession):
    repository = ToolRepository(db_session)
    return repository.create_tool(request.name, request.description)


@toolRoutes.put("/{tool_id}", response_model=ToolResponse)
def update_existing_tool(
    request: ToolRequest, tool_id: int, admin: GetAdminDep, db_session: GetDbSession
):
    repository = ToolRepository(db_session)
    result = repository.update_tool(tool_id, request.name, request.description)
    return ToolResponse.model_validate(result)


@toolRoutes.delete("/{tool_id}", response_model=GenericResponse)
def remove_existing_tool(tool_id: int, admin: GetAdminDep, db_session: GetDbSession):
    repository = ToolRepository(db_session)
    repository.remove_tool(tool_id)
    return {"success": "La herramienta fue eliminada con éxito"}
