from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from ..base import Session
from ..models import File, User


class FileRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_file(self, user_id: int, file_name: str, file_name_saved: str):
        try:
            new_file = File(user_id, file_name, file_name_saved)
            self.session.add(new_file)
            self.session.commit()
            return new_file
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error creating the file in the DB: {e}')

    def get_all_files_from_user(self, user_id: int):
        try:
            user = self.session.get(User, user_id)

            if not user:
                raise Exception(f'User with ID {user_id} not found')

            files = self.session.scalars(
                select(File)
                .join(File.user)
                .where(File.user_id == user_id)
            ).unique().all()

            return files
        except SQLAlchemyError as e:
            raise Exception(f'Error looking for user in the DB: {e}')

    def get_all_files(self):
        try:
            files = self.session.execute(
                select(File).options(joinedload(File.user))
            ).scalars().all()

            return files
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving files from the DB: {e}')

    def get_file_by_id(self, id: int):
        try:
            file = self.session.get(File, id)
            if not file:
                raise Exception(f'File with ID {id} was not found')
            return file
        except SQLAlchemyError as e:
            raise Exception(f'Error looking for file with ID {id} in the DB: {e}')

    def update_file(self, id: int, user_id: int, file_name: str, file_name_saved: str):
        try:
            file = self.session.get(File, id)
            if not file:
                raise Exception(f'File with ID {id} was not found')

            file.user_id = user_id
            file.file_path = file_name_saved
            file.file_name = file_name
            self.session.commit()
            return file
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error updating the file in the DB: {e}')

    def remove_file(self, id: int):
        try:
            file = self.session.get(File, id)
            if not file:
                raise Exception(f'File with ID {id} was not found')

            self.session.delete(file)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error removing the file from the DB: {e}')

    def close_session(self):
        self.session.close()
