from core.domain.types import FileReport
from fastapi import APIRouter, HTTPException, UploadFile
from manager.adapters.api.middleware.authMiddleware import GetAdminDep, GetUserDep
from manager.adapters.api.middleware.contextMiddleware import GetFileService
from manager.adapters.api.schemas.files import FileContentResponse, FileResponse, FileUpdate
from manager.adapters.api.schemas.general import GenericResponse

fileRoutes = APIRouter(prefix="/files", tags=["Files"])


@fileRoutes.get("", response_model_by_alias=False)
@fileRoutes.get("/", response_model_by_alias=False)
def get_files(user: GetUserDep, file_service: GetFileService) -> list[FileResponse]:
    if user.id is None:
        raise HTTPException(500, detail="User ID is required")

    files = file_service.get_all_files_from_user(user.id)

    return [FileResponse.model_validate(file) for file in files]


@fileRoutes.get("/all", response_model_by_alias=False)
def get_files_from_all_users(
    admin: GetAdminDep, file_service: GetFileService
) -> list[FileResponse]:
    files = file_service.get_all_files()

    return [FileResponse.model_validate(file) for file in files]


@fileRoutes.get("/{file_id}", response_model_by_alias=False, response_model=FileResponse)
def get_file(file_id: int, user: GetUserDep, file_service: GetFileService):
    result = file_service.get_file_by_id(file_id)
    return FileResponse.model_validate(result)


@fileRoutes.get("/{file_id}/content", response_model=FileContentResponse)
def get_file_content(file_id: int, user: GetUserDep, file_service: GetFileService):
    return {"content": file_service.read_file(file_id)}


@fileRoutes.get("/{file_id}/report")
def get_file_report(file_id: int, user: GetUserDep, file_service: GetFileService) -> FileReport:
    file = file_service.get_file_by_id(file_id)
    return file.report


@fileRoutes.post("", response_model_by_alias=False, response_model=FileResponse)
@fileRoutes.post("/", response_model_by_alias=False, response_model=FileResponse)
def upload_file(file: UploadFile, user: GetUserDep, file_service: GetFileService):
    if user.id is None:
        raise HTTPException(500, detail="User ID is required")

    if not file.filename:
        raise HTTPException(400, detail="Filename is required")
    new_file = file_service.upload_file(user.id, file.filename, file.file)

    if new_file.id is None:
        raise HTTPException(500, detail="File creation failed - no ID assigned")

    return new_file


@fileRoutes.put("/{file_id}", response_model_by_alias=False, response_model=FileResponse)
def update_file_name(
    file_id: int, request: FileUpdate, user: GetUserDep, file_service: GetFileService
):
    if user.id is None:
        raise HTTPException(500, detail="User ID is required")

    result = file_service.rename_file_by_id(user.id, file_id, request.file_name)
    return FileResponse.model_validate(result)


@fileRoutes.delete("/{file_id}", response_model=GenericResponse)
def remove_existing_file(file_id: int, user: GetUserDep, file_service: GetFileService):
    file_service.remove_file_by_id(file_id)
    return {"success": "El archivo fue eliminado con éxito"}


@fileRoutes.post("/{file_id}/thumbnail", response_model=GenericResponse)
def generate_thumbnail(file_id: int, admin: GetAdminDep, file_service: GetFileService):
    file_service.create_thumbnail(file_id)
    return {"success": "La generación de la vista previa fue solicitada con éxito"}


@fileRoutes.post("/{file_id}/report", response_model=GenericResponse)
def generate_report(file_id: int, admin: GetAdminDep, file_service: GetFileService):
    file_service.generate_file_report(file_id)
    return {"success": "La generación del reporte fue solicitada con éxito"}
