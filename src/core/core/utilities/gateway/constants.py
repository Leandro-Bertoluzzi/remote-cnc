"""Shared constants for CNC Gateway communication.

Used by both the Gateway process and the GatewayClient (API, Worker, Desktop).
See DR-0003 for the priority queue design.
"""

# ---------------------------------------------------------------------------
# Redis key prefixes
# ---------------------------------------------------------------------------

# Priority command queues (consumed via BLPOP in this order)
QUEUE_CRITICAL = "cnc:queue:critical"
QUEUE_HIGH = "cnc:queue:high"
QUEUE_NORMAL = "cnc:queue:normal"

ALL_QUEUES = [QUEUE_CRITICAL, QUEUE_HIGH, QUEUE_NORMAL]

# Session lock key
SESSION_KEY = "cnc:session"

# Gateway state key (published periodically)
GATEWAY_STATE_KEY = "cnc:gateway_state"

# Last published status (JSON snapshot for REST polling)
LAST_STATUS_KEY = "cnc:last_status"

# ---------------------------------------------------------------------------
# PubSub channels
# ---------------------------------------------------------------------------

STATUS_CHANNEL = "grbl_status"
MESSAGES_CHANNEL = "grbl_messages"
EVENTS_CHANNEL = "cnc:events"

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
# Event types (published on EVENTS_CHANNEL)
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
# Session defaults
# ---------------------------------------------------------------------------

SESSION_TTL_SECONDS = 300  # 5 minutes
