from database.models import Task
from database.repositories.taskRepository import TaskRepository
import pytest
from sqlalchemy.exc import SQLAlchemyError


class TestTaskRepository:
    def test_create_task(self, mocked_session):
        task_repository = TaskRepository(mocked_session)
        user_id = 1
        file_id = 1
        tool_id = 1
        material_id = 1
        name = 'New Task'
        note = 'This is a note'

        # Call method under test
        new_task = task_repository.create_task(
            user_id,
            file_id,
            tool_id,
            material_id,
            name,
            note
        )

        # Assertions
        assert new_task is not None
        assert isinstance(new_task, Task)
        assert new_task.id is not None
        assert new_task.user_id == user_id
        assert new_task.file_id == file_id
        assert new_task.tool_id == tool_id
        assert new_task.material_id == material_id
        assert new_task.name == name
        assert new_task.note == note

    def test_get_all_tasks_from_user(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call method under test and assert result
        tasks = task_repository.get_all_tasks_from_user(user_id=1)
        assert isinstance(tasks, list)

        tasks = task_repository.get_all_tasks_from_user(user_id=1, status='on_hold')
        assert isinstance(tasks, list)

    def test_get_all_tasks(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call method under test and assert result
        tasks = task_repository.get_all_tasks()
        assert isinstance(tasks, list)

        tasks = task_repository.get_all_tasks(status='on_hold')
        assert isinstance(tasks, list)

    def test_get_next_task(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call method under test and assert result
        task = task_repository.get_next_task()
        assert isinstance(task, Task)
        assert task.id is not None
        assert task.user_id == 1
        assert task.file_id == 1
        assert task.tool_id == 1
        assert task.material_id == 1
        assert task.name == 'Task 2'
        assert task.note == 'This is a note'
        assert task.status == 'on_hold'

    def test_are_there_tasks_with_status(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call method under test and assert result
        result = task_repository.are_there_tasks_with_status('pending_approval')
        assert result is True

        # Call method under test and assert result
        result = task_repository.are_there_tasks_with_status('in_progress')
        assert result is False

    def test_are_there_pending_tasks(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call method under test and assert result
        result = task_repository.are_there_pending_tasks()
        assert result is True

    def test_are_there_tasks_in_progress(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call method under test and assert result
        result = task_repository.are_there_tasks_in_progress()
        assert result is False

    def test_update_task(self, mocked_session):
        task_repository = TaskRepository(mocked_session)
        user_id = 1
        file_id = 1
        tool_id = 1
        material_id = 1
        name = 'Updated Task'
        note = 'This is an updated note'
        priority = 80

        # Call method under test
        updated_task = task_repository.update_task(
            1,
            user_id,
            file_id,
            tool_id,
            material_id,
            name,
            note,
            priority
        )

        # Assertions
        assert updated_task.user_id == user_id
        assert updated_task.file_id == file_id
        assert updated_task.tool_id == tool_id
        assert updated_task.material_id == material_id
        assert updated_task.name == name
        assert updated_task.note == note
        assert updated_task.priority == priority

    @pytest.mark.parametrize(
            'status,expected_admin_id,expected_cancellation_reason',
            [
                ('pending_approval', None, None),
                ('on_hold', 1, None),
                ('rejected', 1, 'This is a valid reason'),
                ('cancelled', None, 'This is a valid reason')
            ]
    )
    def test_update_task_status(
        self,
        mocked_session,
        status,
        expected_admin_id,
        expected_cancellation_reason
    ):
        task_repository = TaskRepository(mocked_session)
        admin_id = 1
        cancellation_reason = 'This is a valid reason'

        # Call method under test
        updated_task = task_repository.update_task_status(
            1,
            status,
            admin_id,
            cancellation_reason
        )

        # Assertions
        assert updated_task.status == status
        assert updated_task.admin_id == expected_admin_id
        assert updated_task.cancellation_reason == expected_cancellation_reason

    def test_update_task_status_back_to_pending(self, mocked_session):
        task_repository = TaskRepository(mocked_session)
        admin_id = 1

        # Call method under test
        updated_task = task_repository.update_task_status(
            2,
            'pending_approval',
            admin_id
        )

        # Assertions
        assert updated_task.status == 'pending_approval'
        assert updated_task.admin_id is None

    def test_remove_task(self, mocked_session):
        task_repository = TaskRepository(mocked_session)
        tasks_before = task_repository.get_all_tasks()

        # Call method under test
        task_repository.remove_task(id=1)

        # Assertions
        tasks_after = task_repository.get_all_tasks()
        assert len(tasks_after) == len(tasks_before) - 1

    def test_error_create_task_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'add', side_effect=SQLAlchemyError('mocked error'))
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.create_task(
                user_id=1,
                file_id=1,
                tool_id=1,
                material_id=1,
                name='name'
            )
        assert 'Error creating the task in the DB' in str(error.value)

    def test_error_get_all_tasks_from_user_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'scalars', side_effect=SQLAlchemyError('mocked error'))
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.get_all_tasks_from_user(user_id=1)
        assert 'Error retrieving tasks from the DB' in str(error.value)

    def test_error_get_all_tasks_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'scalars', side_effect=SQLAlchemyError('mocked error'))
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.get_all_tasks()
        assert 'Error retrieving tasks from the DB' in str(error.value)

    def test_error_get_next_task_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'scalars', side_effect=SQLAlchemyError('mocked error'))
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.get_next_task()
        assert 'Error retrieving tasks from the DB' in str(error.value)

    def test_error_update_non_existing_task(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.update_task(id=5000, user_id=1)
        assert str(error.value) == 'Task with ID 5000 was not found for this user'

    def test_error_update_task_from_another_user(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.update_task(id=1, user_id=2)
        assert str(error.value) == 'Task with ID 1 was not found for this user'

    def test_error_update_task_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.update_task(id=1, user_id=1)
        assert 'Error updating task with ID 1 in DB' in str(error.value)

    def test_error_update_status_for_non_existing_task(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.update_task_status(id=5000, status='on_hold')
        assert str(error.value) == 'Task with ID 5000 was not found'

    def test_error_update_non_valid_status(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.update_task_status(id=1, status='invalid_status')
        assert str(error.value) == 'Status invalid_status is not valid'

    def test_error_update_needed_admin(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.update_task_status(id=1, status='on_hold')
        assert str(error.value) == 'Admin level is required to perform the action'

    def test_error_update_task_status_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.update_task_status(id=1, status='on_hold')
        assert 'Error updating the task status in the DB' in str(error.value)

    def test_error_remove_non_existing_task(self, mocked_session):
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.remove_task(id=5000)
        assert str(error.value) == 'Task with ID 5000 was not found'

    def test_error_remove_task_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'get', side_effect=SQLAlchemyError('mocked error'))
        task_repository = TaskRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            task_repository.remove_task(id=1)
        assert 'Error removing the task from the DB' in str(error.value)
