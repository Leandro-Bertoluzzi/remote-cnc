from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, Session
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional
from database.exceptions import DatabaseError, EntityNotFoundError, Unauthorized
from database.models import Task, TaskStatus, TASK_EMPTY_NOTE
from utilities.validators import validate_transition, is_valid_task_state


# Custom exceptions
class InvalidTaskStatus(Exception):
    pass


class TaskRepository:
    def __init__(self, _session: Session):
        self.session = _session

    def create_task(
        self,
        user_id: int,
        file_id: int,
        tool_id: int,
        material_id: int,
        name: str,
        note: str = TASK_EMPTY_NOTE
    ):
        try:
            new_task = Task(
                user_id,
                file_id,
                tool_id,
                material_id,
                name,
                note
            )

            self.session.add(new_task)
            self.session.commit()
            return new_task
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error creating the task in the DB: {e}')

    def get_task_by_id(self, id: int):
        try:
            query = select(
                Task
            ).options(
                joinedload(Task.file),
                joinedload(Task.material),
                joinedload(Task.tool),
                joinedload(Task.user)
            )
            task = self.session.scalars(
                query.where(Task.id == id)
            ).unique().first()
            return task
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error looking for task with ID {id} in the DB: {e}')

    def _get_filtered_tasks(
            self,
            user_id: Optional[int],
            status: str,
            order_criterion=Task.priority.asc()
    ):
        query = select(
            Task
        ).options(
            joinedload(Task.file),
            joinedload(Task.material),
            joinedload(Task.tool),
            joinedload(Task.user)
        )

        if user_id:
            query = query.where(Task.user_id == user_id)
        if status != 'all':
            query = query.where(Task.status == status)
        return self.session.scalars(
            query.order_by(order_criterion)
        ).unique().all()

    def get_all_tasks_from_user(self, user_id: int, status: str = 'all'):
        try:
            tasks = self._get_filtered_tasks(user_id, status)
            return tasks
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error retrieving tasks from the DB: {e}')

    def get_all_tasks(self, status: str = 'all'):
        try:
            tasks = self._get_filtered_tasks(user_id=None, status=status)
            return tasks
        except SQLAlchemyError as e:
            raise DatabaseError(f'Error retrieving tasks from the DB: {e}')

    def are_there_tasks_with_status(self, status: str) -> bool:
        query = select(func.count()).select_from(Task).where(Task.status == status)
        count = self.session.execute(query).scalar_one()
        return count > 0

    def are_there_pending_tasks(self) -> bool:
        return self.are_there_tasks_with_status(TaskStatus.APPROVED.value)

    def are_there_tasks_in_progress(self) -> bool:
        return self.are_there_tasks_with_status(TaskStatus.IN_PROGRESS.value)

    def update_task(
        self,
        id: int,
        user_id: int,
        file_id: Optional[int] = None,
        tool_id: Optional[int] = None,
        material_id: Optional[int] = None,
        name: Optional[str] = None,
        note: Optional[str] = None,
        priority: Optional[int] = None,
    ):
        try:
            task = self.session.get(Task, id)
            if not task or task.user_id != user_id:
                raise EntityNotFoundError(f'Task with ID {id} was not found for this user')

            task.file_id = file_id or task.file_id
            task.tool_id = tool_id or task.tool_id
            task.material_id = material_id or task.material_id
            task.name = name or task.name
            task.note = note or task.note
            task.priority = priority or task.priority

            self.session.commit()
            self.session.refresh(task)
            return task
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error updating task with ID {id} in DB: {e}')

    def update_task_status(
        self,
        id: int,
        status: str,
        admin_id: Optional[int] = None,
        cancellation_reason: str = "",
    ):
        if not is_valid_task_state(status):
            raise InvalidTaskStatus(f'Status {status} is not valid')

        try:
            task = self.session.get(Task, id)
            if not task:
                raise EntityNotFoundError(f'Task with ID {id} was not found')

            if task.status == status:
                return task

            if not validate_transition(task.status, status):
                raise InvalidTaskStatus(f'Transition from {task.status} to {status} is not valid')

            is_pending = task.status == TaskStatus.PENDING_APPROVAL.value
            approved = is_pending and status == TaskStatus.APPROVED.value

            if approved:
                if not admin_id:
                    raise Unauthorized('Admin level is required to perform the action')
                task.admin_id = admin_id

            if status == TaskStatus.PENDING_APPROVAL.value:
                task.cancellation_reason = None
                task.admin_id = None

            if status == TaskStatus.CANCELLED.value:
                task.cancellation_reason = cancellation_reason

            task.status = status
            task.status_updated_at = datetime.now()

            self.session.commit()
            self.session.refresh(task)
            return task
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error updating the task status in the DB: {e}')

    def remove_task(self, id: int):
        try:
            task = self.session.get(Task, id)
            if not task:
                raise EntityNotFoundError(f'Task with ID {id} was not found')

            self.session.delete(task)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f'Error removing the task from the DB: {e}')

    def close_session(self):
        self.session.close()
