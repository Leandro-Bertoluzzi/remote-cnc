from fastapi import APIRouter

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.dbMiddleware import GetToolRepository
from api.schemas.general import GenericResponse
from api.schemas.tools import ToolRequest, ToolResponse

toolRoutes = APIRouter(prefix="/tools", tags=["Tools"])


@toolRoutes.get("")
@toolRoutes.get("/")
@toolRoutes.get("/all")
def get_tools(user: GetUserDep, repository: GetToolRepository) -> list[ToolResponse]:
    tools = repository.get_all_tools()

    return [ToolResponse.model_validate(tool) for tool in tools]


@toolRoutes.get("/{tool_id}", response_model=ToolResponse)
def get_tool_by_id(tool_id: int, user: GetUserDep, repository: GetToolRepository):
    result = repository.get_tool_by_id(tool_id)
    return ToolResponse.model_validate(result)


@toolRoutes.post("", response_model=ToolResponse)
@toolRoutes.post("/", response_model=ToolResponse)
def create_new_tool(request: ToolRequest, admin: GetAdminDep, repository: GetToolRepository):
    return repository.create_tool(request.name, request.description)


@toolRoutes.put("/{tool_id}", response_model=ToolResponse)
def update_existing_tool(
    request: ToolRequest, tool_id: int, admin: GetAdminDep, repository: GetToolRepository
):
    result = repository.update_tool(tool_id, request.name, request.description)
    return ToolResponse.model_validate(result)


@toolRoutes.delete("/{tool_id}", response_model=GenericResponse)
def remove_existing_tool(tool_id: int, admin: GetAdminDep, repository: GetToolRepository):
    repository.remove_tool(tool_id)
    return {"success": "La herramienta fue eliminada con éxito"}
