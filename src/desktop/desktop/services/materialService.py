"""Service layer for Material domain operations."""

from core.domain.entities import Material
from core.ports.db_session import SessionFactory

from desktop.services.dependencies import get_material_repository


class MaterialService:
    """Encapsulates all material-related database operations."""

    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    def get_all_materials(self) -> list[Material]:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_material_repository(session)
            return repository.get_all_materials()

    def create_material(self, name: str, description: str) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_material_repository(session)
            repository.create_material(name, description)

    def update_material(self, material_id: int, name: str, description: str) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_material_repository(session)
            repository.update_material(material_id, name, description)

    def remove_material(self, material_id: int) -> None:
        with self._session_factory(expire_on_commit=False) as session:
            repository = get_material_repository(session)
            repository.remove_material(material_id)
