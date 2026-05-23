from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from core.adapters.database.mappers import to_file_domain
from core.adapters.database.models import File, User
from core.domain.exceptions import (
    DuplicatedFileError,
    DuplicatedFileNameError,
    EntityNotFoundError,
    PersistenceError,
)
from core.domain.types import FileReport
from core.ports.db_session import DbSession
from core.ports.file_repository import IFileRepository


class FileRepository(IFileRepository):
    def __init__(self, _session: DbSession):
        self.session = _session

    def check_file_exists(self, user_id: int, file_name: str, file_hash: str):
        repeated = (
            self.session.scalars(
                select(File).where(File.file_name == file_name, File.user_id == user_id)
            )
            .unique()
            .all()
        )

        if repeated:
            raise DuplicatedFileNameError(f"Ya existe un archivo con el nombre <<{file_name}>>")

        duplicated = self.session.scalars(
            select(File).where(File.file_hash == file_hash, File.user_id == user_id)
        ).first()

        if duplicated:
            raise DuplicatedFileError(
                f"El archivo <<{duplicated.file_name}>> tiene el mismo contenido"
            )

    def create_file(self, user_id: int, file_name: str, file_hash: str):
        try:
            new_file = File(user_id, file_name, file_hash)
            self.session.add(new_file)
            self.session.commit()
            self.session.refresh(new_file)
            return to_file_domain(new_file, include_user=False)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error creating the file in the DB: {e}") from e

    def get_all_files_from_user(self, user_id: int):
        try:
            user = self.session.get(User, user_id)

            if not user:
                raise EntityNotFoundError(f"User with ID {user_id} not found")

            files = (
                self.session.scalars(
                    select(File).options(joinedload(File.user)).where(File.user_id == user_id)
                )
                .unique()
                .all()
            )

            return [to_file_domain(file) for file in files]
        except SQLAlchemyError as e:
            raise PersistenceError(f"Error looking for user in the DB: {e}") from e

    def get_all_files(self):
        try:
            files = self.session.scalars(select(File).options(joinedload(File.user))).all()

            return [to_file_domain(file) for file in files]
        except SQLAlchemyError as e:
            raise PersistenceError(f"Error retrieving files from the DB: {e}") from e

    def get_file_by_id(self, id: int):
        try:
            file = self.session.scalars(
                select(File).options(joinedload(File.user)).where(File.id == id)
            ).first()
            if not file:
                raise EntityNotFoundError(f"File with ID {id} was not found")
            return to_file_domain(file)
        except SQLAlchemyError as e:
            raise PersistenceError(f"Error looking for file with ID {id} in the DB: {e}") from e

    def update_file(self, id: int, user_id: int, file_name: str, file_hash: Optional[str] = None):
        try:
            file = self.session.get(File, id)
            if not file:
                raise EntityNotFoundError(f"File with ID {id} was not found")

            file.user_id = user_id
            file.file_name = file_name
            if file_hash:
                file.file_hash = file_hash
            self.session.commit()
            self.session.refresh(file)
            return to_file_domain(file, include_user=False)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error updating the file in the DB: {e}") from e

    def save_file_report(self, id: int, report: FileReport):
        try:
            file = self.session.get(File, id)
            if not file:
                raise EntityNotFoundError(f"File with ID {id} was not found")

            file.report = report
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error updating the file in the DB: {e}") from e

    def remove_file(self, id: int):
        try:
            file = self.session.get(File, id)
            if not file:
                raise EntityNotFoundError(f"File with ID {id} was not found")

            self.session.delete(file)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PersistenceError(f"Error removing the file from the DB: {e}") from e
