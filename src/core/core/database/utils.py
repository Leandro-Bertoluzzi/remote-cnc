from core.database.base import SessionLocal
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.toolRepository import ToolRepository


def get_assets(user_id: int):
    db_session = SessionLocal()
    files_repository = FileRepository(db_session)
    materials_repository = MaterialRepository(db_session)
    tools_repository = ToolRepository(db_session)

    files = files_repository.get_all_files_from_user(user_id)
    materials = materials_repository.get_all_materials()
    tools = tools_repository.get_all_tools()

    return files, materials, tools
