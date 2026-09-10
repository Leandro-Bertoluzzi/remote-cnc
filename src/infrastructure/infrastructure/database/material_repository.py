from __future__ import annotations

from core.domain.exceptions import EntityNotFoundError, PersistenceError
from core.ports.db_session import DbSession
from core.ports.material_repository import IMaterialRepository
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from infrastructure.database.mappers import to_material_domain
from infrastructure.database.models import Material


class MaterialRepository(IMaterialRepository):
    def __init__(self, _session: DbSession):
        self.session = _session

    def create_material(self, name: str, description: str):
        try:
            new_material = Material(name, description)
            self.session.add(new_material)
            self.session.commit()
            self.session.refresh(new_material)
            return to_material_domain(new_material)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error creating the material in the DB: {e}") from e

    def get_material_by_id(self, id: int):
        try:
            material = self.session.get(Material, id)
            if not material:
                raise EntityNotFoundError(f"Material with ID {id} was not found")
            return to_material_domain(material)
        except SQLAlchemyError as e:
            raise PersistenceError(f"Error retrieving the material with ID {id}: {e}") from e

    def get_all_materials(self):
        try:
            materials = self.session.scalars(select(Material)).all()
            return [to_material_domain(material) for material in materials]
        except SQLAlchemyError as e:
            raise PersistenceError(f"Error retrieving materials from the DB: {e}") from e

    def update_material(self, id: int, name: str, description: str):
        try:
            material = self.session.get(Material, id)
            if not material:
                raise EntityNotFoundError(f"Material with ID {id} was not found")

            material.name = name
            material.description = description
            self.session.commit()
            self.session.refresh(material)
            return to_material_domain(material)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error updating the material in the DB: {e}") from e

    def remove_material(self, id: int):
        try:
            material = self.session.get(Material, id)
            if not material:
                raise EntityNotFoundError(f"Material with ID {id} was not found")

            self.session.delete(material)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error removing the material from the DB: {e}") from e
