from core.utilities.storage import delete_value, get_value, set_value

# Constants (keys)
WORKER_IS_ENABLED_KEY = "worker_enabled"


class WorkerStoreAdapter:
    """Redis-backed flags for device availability.

    Note: pause/resume is now handled entirely by the Gateway's realtime command queue.
    """

    @classmethod
    def is_device_enabled(cls):
        return not not get_value(WORKER_IS_ENABLED_KEY)

    @classmethod
    def set_device_enabled(cls, enabled: bool):
        if enabled:
            return set_value(WORKER_IS_ENABLED_KEY, "True")

        delete_value(WORKER_IS_ENABLED_KEY)
