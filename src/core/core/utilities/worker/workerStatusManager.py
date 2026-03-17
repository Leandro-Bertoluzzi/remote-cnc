from core.utilities.storage import delete_value, get_value, set_value

# Constants (keys)
WORKER_IS_ENABLED_KEY = "worker_enabled"
WORKER_IS_PAUSED_KEY = "worker_paused"


class WorkerStoreAdapter:
    @classmethod
    def is_device_enabled(cls):
        return not not get_value(WORKER_IS_ENABLED_KEY)

    @classmethod
    def set_device_enabled(cls, enabled: bool):
        if enabled:
            return set_value(WORKER_IS_ENABLED_KEY, "True")

        delete_value(WORKER_IS_ENABLED_KEY)

    @classmethod
    def is_device_paused(cls):
        return not not get_value(WORKER_IS_PAUSED_KEY)

    @classmethod
    def set_device_paused(cls, paused: bool):
        if paused:
            return set_value(WORKER_IS_PAUSED_KEY, "True")

        delete_value(WORKER_IS_PAUSED_KEY)
