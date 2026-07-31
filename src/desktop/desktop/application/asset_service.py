"""Application service for cross-cutting asset queries."""

from collections.abc import Callable

from core.domain.entities import File, Material, Tool
from core.ports.db_session import DbSession, SessionFactory
from core.ports.file_repository import IFileRepository
from core.ports.material_repository import IMaterialRepository
from core.ports.tool_repository import IToolRepository


class AssetService:
    """Provides combined asset queries used across multiple views."""

    def __init__(
        self,
        session_factory: SessionFactory,
        file_repo_factory: Callable[[DbSession], IFileRepository],
        material_repo_factory: Callable[[DbSession], IMaterialRepository],
        tool_repo_factory: Callable[[DbSession], IToolRepository],
    ):
        self._session_factory = session_factory
        self._file_repo_factory = file_repo_factory
        self._material_repo_factory = material_repo_factory
        self._tool_repo_factory = tool_repo_factory

    def get_assets(self, user_id: int) -> tuple[list[File], list[Material], list[Tool]]:
        """Retrieve files (for user), materials, and tools in a single session."""
        with self._session_factory(expire_on_commit=False) as session:
            files_repo = self._file_repo_factory(session)
            materials_repo = self._material_repo_factory(session)
            tools_repo = self._tool_repo_factory(session)

            files = files_repo.get_all_files_from_user(user_id)
            materials = materials_repo.get_all_materials()
            tools = tools_repo.get_all_tools()

            return files, materials, tools
