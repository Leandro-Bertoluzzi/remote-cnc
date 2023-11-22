from database.models import File
from database.repositories.fileRepository import FileRepository
import pytest
from sqlalchemy.exc import SQLAlchemyError


class TestFileRepository:
    def test_create_file(self, mocked_session):
        file_repository = FileRepository(mocked_session)
        user_id = 1
        file_name = 'new-file.gcode'
        file_name_saved = 'path/to/files/new-file.gcode'

        # Call method under test
        new_file = file_repository.create_file(user_id, file_name, file_name_saved)

        # Assertions
        assert new_file is not None
        assert isinstance(new_file, File)
        assert new_file.id is not None
        assert new_file.user_id == user_id
        assert new_file.file_name == file_name
        assert new_file.file_path == file_name_saved

    def test_get_all_files_from_user(self, mocked_session):
        file_repository = FileRepository(mocked_session)

        # Call method under test
        files = file_repository.get_all_files_from_user(user_id=1)

        # Assertions
        assert isinstance(files, list)
        assert len(files) == 2

    def test_get_all_files(self, mocked_session):
        file_repository = FileRepository(mocked_session)

        # Call method under test
        files = file_repository.get_all_files()

        # Assertions
        assert isinstance(files, list)
        assert len(files) == 2

    def test_get_file_by_id(self, mocked_session):
        file_repository = FileRepository(mocked_session)

        # Call method under test
        file = file_repository.get_file_by_id(id=1)

        # Assertions
        assert file is not None
        assert isinstance(file, File)
        assert file.id is not None

    def test_update_file(self, mocked_session):
        file_repository = FileRepository(mocked_session)
        user_id = 1
        file_name = 'updated-file.gcode'
        file_name_saved = 'path/to/files/new-file.gcode'

        # Call method under test
        updated_file = file_repository.update_file(1, user_id, file_name, file_name_saved)

        # Assertions
        assert updated_file.user_id == user_id
        assert updated_file.file_name == file_name
        assert updated_file.file_path == file_name_saved

    def test_remove_file(self, mocked_session):
        file_repository = FileRepository(mocked_session)
        files_before = file_repository.get_all_files()

        # Call method under test
        file_repository.remove_file(id=1)

        # Assertions
        files_after = file_repository.get_all_files()
        assert len(files_after) == len(files_before) - 1

    def test_error_create_file_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'add', side_effect=SQLAlchemyError('mocked error'))
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.create_file(
                user_id=1,
                file_name='name.gcode',
                file_name_saved='path/to/files/name.gcode'
            )
        assert 'Error creating the file in the DB' in str(error.value)

    def test_error_get_all_files_from_non_existing_user(self, mocked_session):
        # Mock DB method to simulate exception
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.get_all_files_from_user(user_id=5000)
        assert str(error.value) == 'User with ID 5000 not found'

    def test_error_get_all_files_from_user_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'execute', side_effect=SQLAlchemyError('mocked error'))
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.get_all_files_from_user(user_id=1)
        assert 'Error looking for user in the DB' in str(error.value)

    def test_error_get_all_files_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'execute', side_effect=SQLAlchemyError('mocked error'))
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.get_all_files()
        assert 'Error retrieving files from the DB' in str(error.value)

    def test_error_get_non_existing_file_by_id(self, mocked_session):
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.get_file_by_id(id=5000)
        assert str(error.value) == 'File with ID 5000 was not found'

    def test_error_get_file_by_id_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.get_file_by_id(id=1)
        assert 'Error looking for file with ID 1 in the DB' in str(error.value)

    def test_error_update_non_existing_file(self, mocked_session):
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.update_file(
                id=5000,
                user_id=1,
                file_name='name.gcode',
                file_name_saved='path/to/files/name.gcode'
            )
        assert str(error.value) == 'File with ID 5000 was not found'

    def test_error_update_file_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.update_file(
                id=1, user_id=1,
                file_name='name.gcode',
                file_name_saved='path/to/files/name.gcode'
            )
        assert 'Error updating the file in the DB' in str(error.value)

    def test_error_remove_non_existing_file(self, mocked_session):
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.remove_file(id=5000)
        assert str(error.value) == 'File with ID 5000 was not found'

    def test_error_remove_file_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        file_repository = FileRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            file_repository.remove_file(id=1)
        assert 'Error removing the file from the DB' in str(error.value)
