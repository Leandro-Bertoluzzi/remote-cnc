from enum import Enum


class TaskStatus(Enum):
    INITIAL = "pending_approval"
    PENDING_APPROVAL = "pending_approval"
    ON_HOLD = "on_hold"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"
    APPROVED = "on_hold"


VALID_ROLES = ["user", "admin"]
TASK_EMPTY_NOTE = ""
TASK_DEFAULT_PRIORITY = 0
