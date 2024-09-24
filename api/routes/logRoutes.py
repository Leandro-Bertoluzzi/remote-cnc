from core.utils.files import changeFileExtension
from core.utils.loggerFactory import get_log_path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from middleware.authMiddleware import GetAdminDep
from schemas.logs import LogsResponse
from utilities.logs import classify_log_files, generate_log_csv

logRoutes = APIRouter(prefix="/logs", tags=["Logs"])


@logRoutes.get('')
@logRoutes.get('/')
@logRoutes.get('/all')
def get_logs(admin: GetAdminDep) -> list[LogsResponse]:
    return classify_log_files()


@logRoutes.get("/{log_name}")
async def get_log_file(log_name: str):
    log_path = get_log_path(log_name)
    if not log_path.exists():
        raise HTTPException(400, detail=str("El archivo no existe"))

    return FileResponse(log_path, media_type='text/plain', filename=log_name)


@logRoutes.get("/{log_name}/csv")
async def get_log_file_csv(log_name: str):
    log_path = get_log_path(log_name)
    if not log_path.exists():
        raise HTTPException(400, detail=str("El archivo no existe"))

    new_name = changeFileExtension(log_name, 'csv')
    headers = {
        'Content-Disposition': f'attachment; filename="{new_name}"'
    }
    return PlainTextResponse(generate_log_csv(log_path), media_type='text/plain', headers=headers)
