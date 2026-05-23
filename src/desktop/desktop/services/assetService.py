"""Service layer for cross-cutting asset queries."""

from core.domain.entities import File, Material, Tool

from desktop.services import get_db_session
from desktop.services.dependencies import (
    get_file_repository,
    get_material_repository,
    get_tool_repository,
)


class AssetService:
    """Provides combined asset queries used across multiple views."""

    @classmethod
    def get_assets(cls, user_id: int) -> tuple[list[File], list[Material], list[Tool]]:
        """Retrieve files (for user), materials, and tools in a single session."""
        with get_db_session() as session:
            files_repo = get_file_repository(session)
            materials_repo = get_material_repository(session)
            tools_repo = get_tool_repository(session)

            files = files_repo.get_all_files_from_user(user_id)
            materials = materials_repo.get_all_materials()
            tools = tools_repo.get_all_tools()

            return files, materials, tools
