from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from typing import Optional
from ..base import Session
from ..exceptions import DatabaseError, EntityNotFoundError
from ..models import File, User


# Custom exceptions
class DuplicatedFileError(Exception):
    pass


class DuplicatedFileNameError(Exception):
    pass


class FileRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def check_file_exists(self, user_id: int, file_name: str, file_hash: str):
        repeated = self.session.scalars(
            select(File)
            .where(
                File.file_name == file_name,
                File.user_id == user_id
            )
        ).unique().all()

        if repeated:
            raise DuplicatedFileNameError(
                f'Ya existe un archivo con el nombre <<{file_name}>>'
            )

        duplicated = self.session.scalars(
            select(File)
            .where(
                File.file_hash == file_hash,
                File.user_id == user_id
            )
        ).first()

        if duplicated:
            raise DuplicatedFileError(
                f'El archivo <<{duplicated.file_name}>> tiene el mismo contenido'
            )

    def create_file(self, user_id: int, file_name: str, file_hash: str):
        try:
            new_file = File(user_id, file_name, file_hash)
            self.session.add(new_file)
            self.session.commit()
            return new_file
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error creating the file in the DB: {e}')

    def get_all_files_from_user(self, user_id: int):
        try:
            user = self.session.get(User, user_id)

            if not user:
                raise EntityNotFoundError(f'User with ID {user_id} not found')

            files = self.session.scalars(
                select(File)
                .join(File.user)
                .where(File.user_id == user_id)
            ).unique().all()

            return files
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error looking for user in the DB: {e}')

    def get_all_files(self):
        try:
            files = self.session.execute(
                select(File).options(joinedload(File.user))
            ).scalars().all()

            return files
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error retrieving files from the DB: {e}')

    def get_file_by_id(self, id: int):
        try:
            file = self.session.get(File, id)
            if not file:
                raise EntityNotFoundError(f'File with ID {id} was not found')
            return file
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error looking for file with ID {id} in the DB: {e}')

    def update_file(self, id: int, user_id: int, file_name: str, file_hash: Optional[str] = None):
        try:
            file = self.session.get(File, id)
            if not file:
                raise EntityNotFoundError(f'File with ID {id} was not found')

            file.user_id = user_id
            file.file_name = file_name
            if file_hash:
                file.file_hash = file_hash
            self.session.commit()
            return file.serialize()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error updating the file in the DB: {e}')

    def remove_file(self, id: int):
        try:
            file = self.session.get(File, id)
            if not file:
                raise EntityNotFoundError(f'File with ID {id} was not found')

            self.session.delete(file)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error removing the file from the DB: {e}')

    def close_session(self):
        self.session.close()
