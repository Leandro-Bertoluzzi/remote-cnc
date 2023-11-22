import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from ..base import Session
from ..models import User, VALID_ROLES


class UserRepository:
    def __init__(self, _session=None):
        self.session = _session or Session()

    def __del__(self):
        self.close_session()

    def create_user(self, name, email, password, role):
        if role not in VALID_ROLES:
            raise Exception(f'ERROR: Role {role} is not valid')

        try:
            user = self.session.scalars(
                select(User).
                filter_by(email=email).
                limit(1)
            ).first()
            if user:
                raise Exception(f'There is already a user registered with the email {email}')

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            new_user = User(name, email, hashed_password, role)
            self.session.add(new_user)
            self.session.commit()
            return new_user
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error creating the user in the DB: {e}')

    def get_all_users(self):
        try:
            users = self.session.execute(
                select(User)
            ).scalars().all()
            return users
        except SQLAlchemyError as e:
            raise Exception(f'Error retrieving users from the DB: {e}')

    def update_user(self, id, name, email, role):
        if role not in VALID_ROLES:
            raise Exception(f'ERROR: Role {role} is not valid')

        try:
            user = self.session.get(User, id)
            if not user:
                raise Exception(f'User with ID {id} was not found')

            user.name = name
            user.email = email
            user.role = role

            self.session.commit()
            return user
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error updating the user in the DB: {e}')

    def remove_user(self, id):
        try:
            user = self.session.get(User, id)
            if not user:
                raise Exception(f'User with ID {id} was not found')

            self.session.delete(user)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f'Error removing the user from the DB: {e}')

    def close_session(self):
        self.session.close()
