from fastapi import APIRouter
from manager.adapters.api.middleware.authMiddleware import GetAdminDep, GetUserDep
from manager.adapters.api.middleware.contextMiddleware import GetToolService
from manager.adapters.api.schemas.general import GenericResponse
from manager.adapters.api.schemas.tools import ToolRequest, ToolResponse

toolRoutes = APIRouter(prefix="/tools", tags=["Tools"])


@toolRoutes.get("")
@toolRoutes.get("/")
@toolRoutes.get("/all")
def get_tools(user: GetUserDep, tool_service: GetToolService) -> list[ToolResponse]:
    tools = tool_service.get_all_tools()

    return [ToolResponse.model_validate(tool) for tool in tools]


@toolRoutes.get("/{tool_id}", response_model=ToolResponse)
def get_tool_by_id(tool_id: int, user: GetUserDep, tool_service: GetToolService):
    result = tool_service.get_tool_by_id(tool_id)
    return ToolResponse.model_validate(result)


@toolRoutes.post("", response_model=ToolResponse)
@toolRoutes.post("/", response_model=ToolResponse)
def create_new_tool(request: ToolRequest, admin: GetAdminDep, tool_service: GetToolService):
    return tool_service.create_tool(request.name, request.description)


@toolRoutes.put("/{tool_id}", response_model=ToolResponse)
def update_existing_tool(
    request: ToolRequest, tool_id: int, admin: GetAdminDep, tool_service: GetToolService
):
    result = tool_service.update_tool(tool_id, request.name, request.description)
    return ToolResponse.model_validate(result)


@toolRoutes.delete("/{tool_id}", response_model=GenericResponse)
def remove_existing_tool(tool_id: int, admin: GetAdminDep, tool_service: GetToolService):
    tool_service.remove_tool(tool_id)
    return {"success": "La herramienta fue eliminada con éxito"}
