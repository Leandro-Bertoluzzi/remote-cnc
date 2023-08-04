from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.base import Session
from database.models.file import File
from database.models.user import User

class FileRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_file(self, user_id, file_name, file_name_saved):
        try:
            new_file = File(user_id, file_name, file_name_saved)
            self.session.add(new_file)
            self.session.commit()
            return new_file
        except SQLAlchemyError as e:
            raise Exception(f'Error creating the file in the DB: {e}')

    def get_all_files_from_user(self, user_id):
        try:
            user = self.session.query(User).options(joinedload(User.files)).get(user_id)
            if not user:
                raise Exception(f'User with ID {user_id} not found')

            return user.files
        except SQLAlchemyError as e:
            raise Exception(f'Error looking for user in the DB: {e}')

    def get_all_files(self):
        try:
            files = self.session.query(File).options(joinedload(File.user)).all()

            return files
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving files from the DB: {e}')

    def get_file_by_id(self, id):
        try:
            file = self.session.query(File).get(id)
            if not file:
                raise Exception(f'File with ID {id} was not found')
            return file
        except SQLAlchemyError as e:
            raise Exception(f'Error looking for file with ID {id} in the DB: {e}')

    def update_file(self, id, user_id, file_name, file_name_saved):
        try:
            file = self.session.query(File).get(id)
            if not file:
                raise Exception(f'File with ID {id} was not found')

            file.user_id = user_id
            file.file_path = file_name_saved
            file.file_name = file_name
            self.session.commit()
            return file
        except SQLAlchemyError as e:
            raise Exception(f'Error updating the file in the DB: {e}')

    def remove_file(self, id):
        try:
            file = self.session.query(File).get(id)
            if not file:
                raise Exception(f'File with ID {id} was not found')

            self.session.delete(file)
            self.session.commit()
        except SQLAlchemyError as e:
            raise Exception(f'Error removing the file from the DB: {e}')

    def close_session(self):
        self.session.close()
