from core.utilities.files import changeFileExtension
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from manager.adapters.api.middleware.authMiddleware import GetAdminDep
from manager.adapters.api.middleware.contextMiddleware import GetLogService
from manager.adapters.api.schemas.logs import LogsResponse

logRoutes = APIRouter(prefix="/logs", tags=["Logs"])


@logRoutes.get("")
@logRoutes.get("/")
@logRoutes.get("/all")
def get_logs(admin: GetAdminDep, log_service: GetLogService) -> list[LogsResponse]:
    return log_service.classify_log_files()


@logRoutes.get("/{log_name}")
async def get_log_file(log_name: str, log_service: GetLogService):
    if not log_service.log_exists(log_name):
        raise HTTPException(400, detail=str("El archivo no existe"))

    log_path = log_service.get_log_path(log_name)
    return FileResponse(log_path, media_type="text/plain", filename=log_name)


@logRoutes.get("/{log_name}/csv")
async def get_log_file_csv(log_name: str, log_service: GetLogService):
    if not log_service.log_exists(log_name):
        raise HTTPException(400, detail=str("El archivo no existe"))

    new_name = changeFileExtension(log_name, "csv")
    headers = {"Content-Disposition": f'attachment; filename="{new_name}"'}
    return PlainTextResponse(
        log_service.generate_log_csv(log_name), media_type="text/plain", headers=headers
    )
