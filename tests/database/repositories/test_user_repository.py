
import bcrypt
from database.models import User
from database.repositories.userRepository import UserRepository
import pytest
from sqlalchemy.exc import SQLAlchemyError


class TestUserRepository:
    def test_create_user(self, mocked_session, mocker):
        user_repository = UserRepository(mocked_session)
        name = 'New User'
        email = 'new.user@email.com'
        password = '1234'
        role = 'user'

        # Test password hashing
        salt = b'$2b$12$Sz3AvkbAmzPN8elw95os.u'
        hashedPassword = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Mock random salt generation for hashing
        mock_gensalt = mocker.patch('bcrypt.gensalt', return_value=salt)

        # Call method under test
        new_user = user_repository.create_user(name, email, password, role)

        # Assertions
        assert mock_gensalt.call_count == 1
        assert new_user is not None
        assert isinstance(new_user, User)
        assert new_user.id is not None
        assert new_user.name == name
        assert new_user.email == email
        assert new_user.password == hashedPassword
        assert new_user.role == role

    def test_get_all_users(self, mocked_session):
        user_repository = UserRepository(mocked_session)

        # Call method under test
        users = user_repository.get_all_users()

        # Assertions
        assert isinstance(users, list)

    def test_update_user(self, mocked_session):
        user_repository = UserRepository(mocked_session)
        updated_name = 'Updated User'
        updated_email = 'updated.user@email.com'
        updated_role = 'admin'

        # Call method under test
        updated_user = user_repository.update_user(1, updated_name, updated_email, updated_role)

        # Assertions
        assert updated_user.name == updated_name
        assert updated_user.email == updated_email
        assert updated_user.role == updated_role

    def test_remove_user(self, mocked_session):
        user_repository = UserRepository(mocked_session)
        users_before = user_repository.get_all_users()

        # Call method under test
        user_repository.remove_user(id=1)

        # Assertions
        users_after = user_repository.get_all_users()
        assert len(users_after) == len(users_before) - 1

    def test_error_create_user_with_invalid_role(self, mocked_session):
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.create_user(
                name='name',
                email='email@email.com',
                password='password',
                role='invalid-role'
            )
        assert str(error.value) == 'ERROR: Role invalid-role is not valid'

    def test_error_create_existing_user(self, mocked_session):
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.create_user(
                name='name',
                email='test@testing.com',
                password='password',
                role='user'
            )
        assert 'There is already a user registered with the email' in str(error.value)

    def test_error_create_user_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'scalars', side_effect=SQLAlchemyError('mocked error'))
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.create_user(
                name='name',
                email='email@email.com',
                password='password',
                role='user'
            )
        assert 'Error creating the user in the DB' in str(error.value)

    def test_error_get_all_users_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'execute', side_effect=SQLAlchemyError('mocked error'))
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.get_all_users()
        assert 'Error retrieving users from the DB' in str(error.value)

    def test_error_update_user_with_invalid_role(self, mocked_session):
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.update_user(
                id=1,
                name='name',
                email='email@email.com',
                role='invalid-role'
            )
        assert str(error.value) == 'ERROR: Role invalid-role is not valid'

    def test_error_update_non_existing_user(self, mocked_session):
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.update_user(
                id=5000,
                name='name',
                email='test@testing.com',
                role='user'
            )
        assert str(error.value) == 'User with ID 5000 was not found'

    def test_error_update_user_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.update_user(id=1, name='name', email='email@email.com', role='user')
        assert 'Error updating the user in the DB' in str(error.value)

    def test_error_remove_non_existing_user(self, mocked_session):
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.remove_user(id=5000)
        assert str(error.value) == 'User with ID 5000 was not found'

    def test_error_remove_user_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        user_repository = UserRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            user_repository.remove_user(id=1)
        assert 'Error removing the user from the DB' in str(error.value)
