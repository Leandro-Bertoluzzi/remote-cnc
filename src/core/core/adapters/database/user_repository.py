from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from core.database.exceptions import (
    DatabaseError,
    DuplicatedUserError,
    EntityNotFoundError,
    InvalidRole,
)
from core.database.models import VALID_ROLES, User
from core.ports.db_session import DbSession
from core.ports.user_repository import IUserRepository
from core.utilities.security import hash_password


class UserRepository(IUserRepository):
    def __init__(self, _session: DbSession):
        self.session = _session

    def create_user(self, name: str, email: str, password: str, role: str):
        if role not in VALID_ROLES:
            raise InvalidRole(f"ERROR: Role {role} is not valid")

        try:
            user = self.session.scalars(select(User).filter_by(email=email)).first()
            if user:
                raise DuplicatedUserError(
                    f"There is already a user registered with the email {email}"
                )

            hashed_password = hash_password(password)

            new_user = User(name, email, hashed_password, role)
            self.session.add(new_user)
            self.session.commit()
            return new_user
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Error creating the user in the DB: {e}") from e

    def get_user_by_id(self, id: int):
        try:
            user = self.session.get(User, id)
            if not user:
                raise EntityNotFoundError(f"User with ID {id} was not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error retrieving the user with ID {id}: {e}") from e

    def get_user_by_email(self, email: str):
        try:
            user = self.session.scalars(select(User).filter_by(email=email)).first()
            return user
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error retrieving the user with email {email}: {e}") from e

    def get_all_users(self):
        try:
            users = self.session.scalars(select(User)).all()
            return users
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error retrieving users from the DB: {e}") from e

    def update_user(self, id: int, name: str, email: str, role: str):
        if role not in VALID_ROLES:
            raise InvalidRole(f"ERROR: Role {role} is not valid")

        try:
            user = self.session.get(User, id)
            if not user:
                raise EntityNotFoundError(f"User with ID {id} was not found")

            user.name = name
            user.email = email
            user.role = role

            self.session.commit()
            self.session.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Error updating the user in the DB: {e}") from e

    def remove_user(self, id: int):
        try:
            user = self.session.get(User, id)
            if not user:
                raise EntityNotFoundError(f"User with ID {id} was not found")

            self.session.delete(user)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Error removing the user from the DB: {e}") from e
