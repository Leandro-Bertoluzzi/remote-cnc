from core.database.repositories.materialRepository import MaterialRepository
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.general import GenericResponseModel
from schemas.materials import MaterialRequestModel, MaterialResponseModel

materialRoutes = APIRouter(prefix="/materials", tags=["Materials"])


@materialRoutes.get('')
@materialRoutes.get('/')
@materialRoutes.get('/all')
def get_materials(
    user: GetUserDep,
    db_session: GetDbSession
) -> list[MaterialResponseModel]:
    repository = MaterialRepository(db_session)
    materials = repository.get_all_materials()

    return [MaterialResponseModel.from_orm(material) for material in materials]


@materialRoutes.post('')
@materialRoutes.post('/')
def create_new_material(
    request: MaterialRequestModel,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> MaterialResponseModel:
    materialName = request.name
    materialDescription = request.description

    try:
        repository = MaterialRepository(db_session)
        return repository.create_material(materialName, materialDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@materialRoutes.put('/{material_id}')
def update_existing_material(
    request: MaterialRequestModel,
    material_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> MaterialResponseModel:
    materialName = request.name
    materialDescription = request.description

    try:
        repository = MaterialRepository(db_session)
        result = repository.update_material(material_id, materialName, materialDescription)
        return MaterialResponseModel.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@materialRoutes.delete('/{material_id}')
def remove_existing_material(
    material_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
) -> GenericResponseModel:
    try:
        repository = MaterialRepository(db_session)
        repository.remove_material(material_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'El material fue eliminado con éxito'}
