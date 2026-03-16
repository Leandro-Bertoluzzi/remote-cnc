"""Service layer for Material domain operations."""

from core.database.models import Material
from core.database.repositories.materialRepository import MaterialRepository

from desktop.services import get_db_session


class MaterialService:
    """Encapsulates all material-related database operations."""

    @classmethod
    def get_all_materials(cls) -> list[Material]:
        with get_db_session() as session:
            repository = MaterialRepository(session)
            return repository.get_all_materials()

    @classmethod
    def create_material(cls, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = MaterialRepository(session)
            repository.create_material(name, description)

    @classmethod
    def update_material(cls, material_id: int, name: str, description: str) -> None:
        with get_db_session() as session:
            repository = MaterialRepository(session)
            repository.update_material(material_id, name, description)

    @classmethod
    def remove_material(cls, material_id: int) -> None:
        with get_db_session() as session:
            repository = MaterialRepository(session)
            repository.remove_material(material_id)
