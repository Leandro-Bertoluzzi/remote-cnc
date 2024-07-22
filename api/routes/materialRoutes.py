from core.database.repositories.materialRepository import MaterialRepository
import datetime
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from pydantic import BaseModel
from services.utilities import serializeList

materialRoutes = APIRouter(prefix="/materials", tags=["Materials"])


class MaterialRequestModel(BaseModel):
    name: str
    description: str


class MaterialResponseModel(BaseModel):
    id: int
    name: str
    description: str
    added_at: datetime.datetime


@materialRoutes.get('')
@materialRoutes.get('/')
@materialRoutes.get('/all')
def get_materials(
    user: GetUserDep,
    db_session: GetDbSession
) -> list[MaterialResponseModel]:
    repository = MaterialRepository(db_session)
    materials = serializeList(repository.get_all_materials())
    return materials


@materialRoutes.post('')
@materialRoutes.post('/')
def create_new_material(
    request: MaterialRequestModel,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> MaterialResponseModel:
    # Get data from request body
    materialName = request.name
    materialDescription = request.description

    try:
        repository = MaterialRepository(db_session)
        material = repository.create_material(materialName, materialDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return material


@materialRoutes.put('/{material_id}')
def update_existing_material(
    request: MaterialRequestModel,
    material_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    materialName = request.name
    materialDescription = request.description

    try:
        repository = MaterialRepository(db_session)
        repository.update_material(material_id, materialName, materialDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The material was successfully updated'}


@materialRoutes.delete('/{material_id}')
def remove_existing_material(
    material_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    try:
        repository = MaterialRepository(db_session)
        repository.remove_material(material_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'The material was successfully removed'}
