"""Service layer for Material domain operations."""

from core.domain.entities import Material

from desktop.services import get_db_session
from desktop.services.dependencies import get_material_repository


class MaterialService:
    """Encapsulates all material-related database operations."""

    @classmethod
    def get_all_materials(cls) -> list[Material]:
        with get_db_session() as session:
            repository = get_material_repository(session)
            return repository.get_all_materials()

    @classmethod
    def create_material(cls, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = get_material_repository(session)
            repository.create_material(name, description)

    @classmethod
    def update_material(cls, material_id: int, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = get_material_repository(session)
            repository.update_material(material_id, name, description)

    @classmethod
    def remove_material(cls, material_id: int) -> None:
        with get_db_session() as session:
            repository = get_material_repository(session)
            repository.remove_material(material_id)
