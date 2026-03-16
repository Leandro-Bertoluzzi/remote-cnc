"""Service layer for cross-cutting asset queries."""

from core.database.models import File, Material, Tool
from core.database.repositories.fileRepository import FileRepository
from core.database.repositories.materialRepository import MaterialRepository
from core.database.repositories.toolRepository import ToolRepository

from desktop.services import get_db_session


class AssetService:
    """Provides combined asset queries used across multiple views."""

    @classmethod
    def get_assets(cls, user_id: int) -> tuple[list[File], list[Material], list[Tool]]:
        """Retrieve files (for user), materials, and tools in a single session."""
        with get_db_session() as session:
            files_repo = FileRepository(session)
            materials_repo = MaterialRepository(session)
            tools_repo = ToolRepository(session)

            files = files_repo.get_all_files_from_user(user_id)
            materials = materials_repo.get_all_materials()
            tools = tools_repo.get_all_tools()

            return files, materials, tools
