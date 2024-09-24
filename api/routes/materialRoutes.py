from core.database.repositories.materialRepository import MaterialRepository
from fastapi import APIRouter, HTTPException
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.general import GenericResponse
from schemas.materials import MaterialRequest, MaterialResponse

materialRoutes = APIRouter(prefix="/materials", tags=["Materials"])


@materialRoutes.get('')
@materialRoutes.get('/')
@materialRoutes.get('/all')
def get_materials(
    user: GetUserDep,
    db_session: GetDbSession
) -> list[MaterialResponse]:
    repository = MaterialRepository(db_session)
    materials = repository.get_all_materials()

    return [MaterialResponse.from_orm(material) for material in materials]


@materialRoutes.post('', response_model=MaterialResponse)
@materialRoutes.post('/', response_model=MaterialResponse)
def create_new_material(
    request: MaterialRequest,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    materialName = request.name
    materialDescription = request.description

    try:
        repository = MaterialRepository(db_session)
        return repository.create_material(materialName, materialDescription)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@materialRoutes.put('/{material_id}', response_model=MaterialResponse)
def update_existing_material(
    request: MaterialRequest,
    material_id: int,
    admin: GetAdminDep,
    db_session: GetDbSession
):
    materialName = request.name
    materialDescription = request.description

    try:
        repository = MaterialRepository(db_session)
        result = repository.update_material(material_id, materialName, materialDescription)
        return MaterialResponse.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@materialRoutes.delete('/{material_id}', response_model=GenericResponse)
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

    return {'success': 'El material fue eliminado con éxito'}
