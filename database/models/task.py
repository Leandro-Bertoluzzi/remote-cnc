from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base
from datetime import datetime

# Enum values
TASK_PENDING_APPROVAL_STATUS = 'pending_approval'
TASK_ON_HOLD_STATUS = 'on_hold'
TASK_IN_PROGRESS_STATUS = 'in_progress'
TASK_FINISHED_STATUS = 'finished'
TASK_REJECTED_STATUS = 'rejected'
TASK_CANCELLED_STATUS = 'cancelled'

VALID_STATUSES = [
    TASK_PENDING_APPROVAL_STATUS,
    TASK_ON_HOLD_STATUS,
    TASK_IN_PROGRESS_STATUS,
    TASK_FINISHED_STATUS,
    TASK_REJECTED_STATUS,
    TASK_CANCELLED_STATUS
]

# Constants
TASK_EMPTY_NOTE = ''
TASK_DEFAULT_PRIORITY = 0
TASK_INITIAL_STATUS = TASK_PENDING_APPROVAL_STATUS

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    status = Column(String)
    priority = Column(Integer)
    note = Column(String)
    created_at = Column(DateTime)
    status_updated_at = Column(DateTime)
    cancellation_reason = Column(String)

    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'))
    file_id = Column(Integer, ForeignKey('files.id'))
    tool_id = Column(Integer, ForeignKey('tools.id'))
    material_id = Column(Integer, ForeignKey('materials.id'))
    admin_id = Column(Integer, ForeignKey('users.id'))

    # Virtual columns
    admin = relationship('User', foreign_keys=[admin_id])

    def __init__(
        self,
        user_id,
        file_id,
        tool_id,
        material_id,
        name,
        note=TASK_EMPTY_NOTE,
        status=TASK_INITIAL_STATUS,
        priority=TASK_DEFAULT_PRIORITY,
        created_at=datetime.now()
    ):
        self.user_id = user_id
        self.file_id = file_id
        self.tool_id = tool_id
        self.material_id = material_id
        self.name = name
        self.note = note
        self.status = status
        self.priority = priority
        self.created_at = created_at

    def __repr__(self):
        return f"<Task: {self.name}, status: {self.status}, created at: {self.created_at}>"
