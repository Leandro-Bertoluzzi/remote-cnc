from core.database.repositories.materialRepository import MaterialRepository
from core.schemas.general import GenericResponse
from core.schemas.materials import MaterialRequest, MaterialResponse
from fastapi import APIRouter

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.dbMiddleware import GetDbSession

materialRoutes = APIRouter(prefix="/materials", tags=["Materials"])


@materialRoutes.get("")
@materialRoutes.get("/")
@materialRoutes.get("/all")
def get_materials(user: GetUserDep, db_session: GetDbSession) -> list[MaterialResponse]:
    repository = MaterialRepository(db_session)
    materials = repository.get_all_materials()

    return [MaterialResponse.model_validate(material) for material in materials]


@materialRoutes.post("", response_model=MaterialResponse)
@materialRoutes.post("/", response_model=MaterialResponse)
def create_new_material(request: MaterialRequest, admin: GetAdminDep, db_session: GetDbSession):
    repository = MaterialRepository(db_session)
    return repository.create_material(request.name, request.description)


@materialRoutes.put("/{material_id}", response_model=MaterialResponse)
def update_existing_material(
    request: MaterialRequest, material_id: int, admin: GetAdminDep, db_session: GetDbSession
):
    repository = MaterialRepository(db_session)
    result = repository.update_material(material_id, request.name, request.description)
    return MaterialResponse.model_validate(result)


@materialRoutes.delete("/{material_id}", response_model=GenericResponse)
def remove_existing_material(material_id: int, admin: GetAdminDep, db_session: GetDbSession):
    repository = MaterialRepository(db_session)
    repository.remove_material(material_id)
    return {"success": "El material fue eliminado con éxito"}
