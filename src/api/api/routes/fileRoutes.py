from core.domain.types import FileReport
from fastapi import APIRouter, HTTPException, UploadFile

from api.middleware.authMiddleware import GetAdminDep, GetUserDep
from api.middleware.dbMiddleware import GetFileRepository
from api.middleware.fileManagerMiddleware import GetFileManager
from api.middleware.workerMiddleware import GetWorker
from api.schemas.files import FileContentResponse, FileResponse, FileUpdate
from api.schemas.general import GenericResponse

fileRoutes = APIRouter(prefix="/files", tags=["Files"])


@fileRoutes.get("", response_model_by_alias=False)
@fileRoutes.get("/", response_model_by_alias=False)
def get_files(user: GetUserDep, repository: GetFileRepository) -> list[FileResponse]:
    files = repository.get_all_files_from_user(user.id)

    return [FileResponse.model_validate(file) for file in files]


@fileRoutes.get("/all", response_model_by_alias=False)
def get_files_from_all_users(
    admin: GetAdminDep, repository: GetFileRepository
) -> list[FileResponse]:
    files = repository.get_all_files()

    return [FileResponse.model_validate(file) for file in files]


@fileRoutes.get("/{file_id}", response_model_by_alias=False, response_model=FileResponse)
def get_file(file_id: int, user: GetUserDep, repository: GetFileRepository):
    result = repository.get_file_by_id(file_id)
    return FileResponse.model_validate(result)


@fileRoutes.get("/{file_id}/content", response_model=FileContentResponse)
def get_file_content(file_id: int, user: GetUserDep, file_manager: GetFileManager):
    return {"content": file_manager.read_file(file_id)}


@fileRoutes.get("/{file_id}/report")
def get_file_report(file_id: int, user: GetUserDep, repository: GetFileRepository) -> FileReport:
    file = repository.get_file_by_id(file_id)
    return file.report


@fileRoutes.post("", response_model_by_alias=False, response_model=FileResponse)
@fileRoutes.post("/", response_model_by_alias=False, response_model=FileResponse)
def upload_file(
    file: UploadFile, user: GetUserDep, file_manager: GetFileManager, worker: GetWorker
):
    if not file.filename:
        raise HTTPException(400, detail="Filename is required")
    new_file = file_manager.upload_file(user.id, file.filename, file.file)
    worker.generate_file_report(new_file.id)
    worker.create_thumbnail(new_file.id)
    return new_file


@fileRoutes.put("/{file_id}", response_model_by_alias=False, response_model=FileResponse)
def update_file_name(
    file_id: int, request: FileUpdate, user: GetUserDep, file_manager: GetFileManager
):
    result = file_manager.rename_file_by_id(user.id, file_id, request.file_name)
    return FileResponse.model_validate(result)


@fileRoutes.delete("/{file_id}", response_model=GenericResponse)
def remove_existing_file(file_id: int, user: GetUserDep, file_manager: GetFileManager):
    file_manager.remove_file_by_id(file_id)
    return {"success": "El archivo fue eliminado con éxito"}


@fileRoutes.post("/{file_id}/thumbnail", response_model=GenericResponse)
def generate_thumbnail(file_id: int, admin: GetAdminDep, worker: GetWorker):
    worker.create_thumbnail(file_id)
    return {"success": "La generación de la vista previa fue solicitada con éxito"}


@fileRoutes.post("/{file_id}/report", response_model=GenericResponse)
def generate_report(file_id: int, admin: GetAdminDep, worker: GetWorker):
    worker.generate_file_report(file_id)
    return {"success": "La generación del reporte fue solicitada con éxito"}
