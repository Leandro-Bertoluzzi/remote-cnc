from sqlalchemy.exc import SQLAlchemyError
from database.base import Session
from database.models.material import Material

class MaterialRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_material(self, name, description):
        try:
            new_material = Material(name, description)
            self.session.add(new_material)
            self.session.commit()
            return new_material
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error creating the material in the DB: {e}')

    def get_all_materials(self):
        try:
            materials = self.session.query(Material).all()
            return materials
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving materials from the DB: {e}')

    def update_material(self, id, name, description):
        try:
            material = self.session.query(Material).get(id)
            if not material:
                raise Exception(f'Material with ID {id} was not found')

            material.name = name
            material.description = description
            self.session.commit()
            return material
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error updating the material in the DB: {e}')

    def remove_material(self, id):
        try:
            material = self.session.query(Material).get(id)
            if not material:
                raise Exception(f'Material with ID {id} was not found')

            self.session.delete(material)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error removing the material from the DB: {e}')

    def close_session(self):
        self.session.close()
