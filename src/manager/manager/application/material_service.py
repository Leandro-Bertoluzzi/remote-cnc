"""Application service for Material domain operations."""

from collections.abc import Callable

from core.domain.entities import Material
from core.ports.db_session import DbSession, SessionFactory
from core.ports.material_repository import IMaterialRepository


class MaterialService:
    """Encapsulates all material-related database operations."""

    def __init__(
        self,
        session_factory: SessionFactory,
        material_repo_factory: Callable[[DbSession], IMaterialRepository],
    ):
        self._session_factory = session_factory
        self._material_repo_factory = material_repo_factory

    def get_all_materials(self) -> list[Material]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._material_repo_factory(session)
            return repository.get_all_materials()

    def create_material(self, name: str, description: str) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._material_repo_factory(session)
            repository.create_material(name, description)

    def update_material(self, material_id: int, name: str, description: str) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._material_repo_factory(session)
            repository.update_material(material_id, name, description)

    def remove_material(self, material_id: int) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = self._material_repo_factory(session)
            repository.remove_material(material_id)
