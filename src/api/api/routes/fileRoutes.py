from core.config import FILES_FOLDER_PATH
from core.database.repositories.fileRepository import FileRepository
from core.database.types import FileReport
from core.schemas.files import FileContentResponse, FileResponse, FileUpdate
from core.schemas.general import GenericResponse
from core.utilities.fileManager import FileManager
from core.utilities.worker.scheduler import create_thumbnail, generate_file_report
from fastapi import APIRouter, HTTPException, UploadFile

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.dbMiddleware import GetDbSession

fileRoutes = APIRouter(prefix="/files", tags=["Files"])


@fileRoutes.get("", response_model_by_alias=False)
@fileRoutes.get("/", response_model_by_alias=False)
def get_files(user: GetUserDep, db_session: GetDbSession) -> list[FileResponse]:
    repository = FileRepository(db_session)
    files = repository.get_all_files_from_user(user.id)

    return [FileResponse.model_validate(file) for file in files]


@fileRoutes.get("/all", response_model_by_alias=False)
def get_files_from_all_users(admin: GetAdminDep, db_session: GetDbSession) -> list[FileResponse]:
    repository = FileRepository(db_session)
    files = repository.get_all_files()

    return [FileResponse.model_validate(file) for file in files]


@fileRoutes.get("/{file_id}", response_model_by_alias=False, response_model=FileResponse)
def get_file(file_id: int, user: GetUserDep, db_session: GetDbSession):
    repository = FileRepository(db_session)
    result = repository.get_file_by_id(file_id)
    return FileResponse.model_validate(result)


@fileRoutes.get("/{file_id}/content", response_model=FileContentResponse)
def get_file_content(file_id: int, user: GetUserDep, db_session: GetDbSession):
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    return {"content": file_manager.read_file(file_id)}


@fileRoutes.get("/{file_id}/report")
def get_file_report(file_id: int, user: GetUserDep, db_session: GetDbSession) -> FileReport:
    repository = FileRepository(db_session)
    file = repository.get_file_by_id(file_id)
    return file.report


@fileRoutes.post("", response_model_by_alias=False, response_model=FileResponse)
@fileRoutes.post("/", response_model_by_alias=False, response_model=FileResponse)
def upload_file(file: UploadFile, user: GetUserDep, db_session: GetDbSession):
    if not file.filename:
        raise HTTPException(400, detail="Filename is required")
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    new_file = file_manager.upload_file(user.id, file.filename, file.file)
    generate_file_report(new_file.id)
    create_thumbnail(new_file.id)
    return new_file


@fileRoutes.put("/{file_id}", response_model_by_alias=False, response_model=FileResponse)
def update_file_name(file_id: int, request: FileUpdate, user: GetUserDep, db_session: GetDbSession):
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    result = file_manager.rename_file_by_id(user.id, file_id, request.file_name)
    return FileResponse.model_validate(result)


@fileRoutes.delete("/{file_id}", response_model=GenericResponse)
def remove_existing_file(file_id: int, user: GetUserDep, db_session: GetDbSession):
    file_manager = FileManager(FILES_FOLDER_PATH, db_session)
    file_manager.remove_file_by_id(file_id)
    return {"success": "El archivo fue eliminado con éxito"}


@fileRoutes.post("/{file_id}/thumbnail", response_model=GenericResponse)
def generate_thumbnail(file_id: int, admin: GetAdminDep):
    create_thumbnail(file_id)
    return {"success": "La generación de la vista previa fue solicitada con éxito"}


@fileRoutes.post("/{file_id}/report", response_model=GenericResponse)
def generate_report(file_id: int, admin: GetAdminDep):
    generate_file_report(file_id)
    return {"success": "La generación del reporte fue solicitada con éxito"}
