from fastapi import APIRouter
from middleware.authMiddleware import GetAdminDep
from schemas.logs import LogsResponseModel
from services.utilities import classify_log_files

logRoutes = APIRouter(prefix="/logs", tags=["Logs"])


@logRoutes.get('')
@logRoutes.get('/')
@logRoutes.get('/all')
def get_logs(
    admin: GetAdminDep
) -> list[LogsResponseModel]:
    return classify_log_files()
