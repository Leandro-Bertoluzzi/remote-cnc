from fastapi import APIRouter
from manager.adapters.api.middleware.authMiddleware import GetAdminDep, GetUserDep
from manager.adapters.api.middleware.contextMiddleware import GetMaterialService
from manager.adapters.api.schemas.general import GenericResponse
from manager.adapters.api.schemas.materials import MaterialRequest, MaterialResponse

materialRoutes = APIRouter(prefix="/materials", tags=["Materials"])


@materialRoutes.get("")
@materialRoutes.get("/")
@materialRoutes.get("/all")
def get_materials(user: GetUserDep, material_service: GetMaterialService) -> list[MaterialResponse]:
    materials = material_service.get_all_materials()

    return [MaterialResponse.model_validate(material) for material in materials]


@materialRoutes.post("", response_model=MaterialResponse)
@materialRoutes.post("/", response_model=MaterialResponse)
def create_new_material(
    request: MaterialRequest, admin: GetAdminDep, material_service: GetMaterialService
):
    return material_service.create_material(request.name, request.description)


@materialRoutes.put("/{material_id}", response_model=MaterialResponse)
def update_existing_material(
    request: MaterialRequest,
    material_id: int,
    admin: GetAdminDep,
    material_service: GetMaterialService,
):
    result = material_service.update_material(material_id, request.name, request.description)
    return MaterialResponse.model_validate(result)


@materialRoutes.delete("/{material_id}", response_model=GenericResponse)
def remove_existing_material(
    material_id: int, admin: GetAdminDep, material_service: GetMaterialService
):
    material_service.remove_material(material_id)
    return {"success": "El material fue eliminado con éxito"}
