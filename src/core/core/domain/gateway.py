"""Gateway domain constants.

These are pure domain concepts — message types, action names, event types,
and gateway states. They do NOT reference any infrastructure.

Used by any module that needs to understand *what* a gateway message means, not *where* it lives.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Message types (in the command queues)
# ---------------------------------------------------------------------------

MSG_COMMAND = "command"
MSG_REALTIME = "realtime"
MSG_FILE_START = "file_start"
MSG_FILE_STOP = "file_stop"
MSG_JOG = "jog"
MSG_QUERY = "query"
MSG_DISCONNECT = "disconnect"

# ---------------------------------------------------------------------------
# Realtime action names (payload for MSG_REALTIME)
# ---------------------------------------------------------------------------

ACTION_PAUSE = "pause"
ACTION_RESUME = "resume"
ACTION_STOP = "stop"
ACTION_SOFT_RESET = "soft_reset"

# ---------------------------------------------------------------------------
# Event types (published on the events channel)
# ---------------------------------------------------------------------------

EVENT_FILE_STARTED = "file_started"
EVENT_FILE_PROGRESS = "file_progress"
EVENT_FILE_FINISHED = "file_finished"
EVENT_FILE_FAILED = "file_failed"
EVENT_SESSION_ACQUIRED = "session_acquired"
EVENT_SESSION_RELEASED = "session_released"

# ---------------------------------------------------------------------------
# Gateway states
# ---------------------------------------------------------------------------

GW_STATE_IDLE = "idle"
GW_STATE_STREAMING = "streaming"
GW_STATE_FILE_EXECUTION = "file_execution"

# ---------------------------------------------------------------------------
# PubSub channel names
# ---------------------------------------------------------------------------

STATUS_CHANNEL = "grbl_status"
MESSAGES_CHANNEL = "grbl_messages"
EVENTS_CHANNEL = "cnc:events"

# ---------------------------------------------------------------------------
# Command priority queue names
# ---------------------------------------------------------------------------

QUEUE_CRITICAL = "cnc:queue:critical"
QUEUE_HIGH = "cnc:queue:high"
QUEUE_NORMAL = "cnc:queue:normal"

ALL_QUEUES = [QUEUE_CRITICAL, QUEUE_HIGH, QUEUE_NORMAL]

# ---------------------------------------------------------------------------
# Key names in key-value store
# ---------------------------------------------------------------------------

SESSION_KEY = "cnc:session"
GATEWAY_STATE_KEY = "cnc:gateway_state"
LAST_STATUS_KEY = "cnc:last_status"
