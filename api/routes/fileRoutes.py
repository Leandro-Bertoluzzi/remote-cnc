from config import FILES_FOLDER_PATH
from core.database.repositories.fileRepository import FileRepository
from core.database.types import FileReport
from core.utils.fileManager import FileManager
from core.worker.scheduler import createThumbnail, generateFileReport
from fastapi import APIRouter, HTTPException, UploadFile
from middleware.authMiddleware import GetAdminDep, GetUserDep
from middleware.dbMiddleware import GetDbSession
from schemas.files import FileResponseModel, FileContentResponseModel, FileUpdateModel
from schemas.general import GenericResponseModel

fileRoutes = APIRouter(prefix="/files", tags=["Files"])


@fileRoutes.get('', response_model_by_alias=False)
@fileRoutes.get('/', response_model_by_alias=False)
def get_files(
    user: GetUserDep,
    db_session: GetDbSession
) -> list[FileResponseModel]:
    repository = FileRepository(db_session)
    files = repository.get_all_files_from_user(user.id)

    return [FileResponseModel.from_orm(file) for file in files]


@fileRoutes.get('/all', response_model_by_alias=False)
def get_files_from_all_users(
    admin: GetAdminDep,
    db_session: GetDbSession
) -> list[FileResponseModel]:
    repository = FileRepository(db_session)
    files = repository.get_all_files()

    return [FileResponseModel.from_orm(file) for file in files]


@fileRoutes.get('/{file_id}', response_model_by_alias=False)
def get_file(
    file_id: int,
    user: GetUserDep,
    db_session: GetDbSession
) -> FileResponseModel:
    repository = FileRepository(db_session)
    try:
        result = repository.get_file_by_id(file_id)
        return FileResponseModel.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@fileRoutes.get('/{file_id}/content')
def get_file_content(
    file_id: int,
    user: GetUserDep,
    db_session: GetDbSession
) -> FileContentResponseModel:
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    try:
        return {'content': file_manager.read_file(file_id)}
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@fileRoutes.get('/{file_id}/report')
def get_file_report(
    file_id: int,
    user: GetUserDep,
    db_session: GetDbSession
) -> FileReport:
    repository = FileRepository(db_session)
    try:
        file = repository.get_file_by_id(file_id)
        return file.report
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@fileRoutes.post('', response_model_by_alias=False)
@fileRoutes.post('/', response_model_by_alias=False)
def upload_file(
    file: UploadFile,
    user: GetUserDep,
    db_session: GetDbSession
) -> FileResponseModel:
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    try:
        new_file = file_manager.upload_file(user.id, file.filename, file.file)
        generateFileReport.delay(new_file.id)
        createThumbnail.delay(new_file.id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return new_file


@fileRoutes.put('/{file_id}', response_model_by_alias=False)
def update_file_name(
    file_id: int,
    request: FileUpdateModel,
    user: GetUserDep,
    db_session: GetDbSession
) -> FileResponseModel:
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    try:
        result = file_manager.rename_file_by_id(user.id, file_id, request.file_name)
        FileResponseModel.from_orm(result)
    except Exception as error:
        raise HTTPException(400, detail=str(error))


@fileRoutes.delete('/{file_id}')
def remove_existing_file(
    file_id: int,
    user: GetUserDep,
    db_session: GetDbSession
) -> GenericResponseModel:
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    try:
        file_manager.remove_file_by_id(file_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'El archivo fue eliminado con éxito'}


@fileRoutes.post('/{file_id}/thumbnail')
def generate_thumbnail(
    file_id: int,
    admin: GetAdminDep
) -> GenericResponseModel:
    try:
        createThumbnail.delay(file_id)
    except Exception as error:
        raise HTTPException(400, detail=str(error))

    return {'success': 'La generación de la vista previa fue solicitada con éxito'}
