from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from ..base import Session
from ..exceptions import DatabaseError, EntityNotFoundError
from ..models import Material


class MaterialRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_material(self, name: str, description: str):
        try:
            new_material = Material(name, description)
            self.session.add(new_material)
            self.session.commit()
            return new_material
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error creating the material in the DB: {e}')

    def get_material_by_id(self, id: int):
        try:
            material = self.session.get(Material, id)
            if not material:
                raise EntityNotFoundError(f'Material with ID {id} was not found')
            return material
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error retrieving the material with ID {id}: {e}')

    def get_all_materials(self):
        try:
            materials = self.session.execute(
                select(Material)
            ).scalars().all()
            return materials
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error retrieving materials from the DB: {e}')

    def update_material(self, id: int, name: str, description: str):
        try:
            material = self.session.get(Material, id)
            if not material:
                raise EntityNotFoundError(f'Material with ID {id} was not found')

            material.name = name
            material.description = description
            self.session.commit()
            return material
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error updating the material in the DB: {e}')

    def remove_material(self, id: int):
        try:
            material = self.session.get(Material, id)
            if not material:
                raise EntityNotFoundError(f'Material with ID {id} was not found')

            self.session.delete(material)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error removing the material from the DB: {e}')

    def close_session(self):
        self.session.close()
