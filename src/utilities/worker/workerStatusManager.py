from utilities.storage import delete_value, get_value, set_value

# Constants (keys)
WORKER_IS_ENABLED_KEY = 'worker_enabled'
WORKER_REQUEST_KEY = 'worker_request'
WORKER_IS_PAUSED_KEY = 'worker_paused'

# Constants (values)
WORKER_PAUSE_REQUEST = 'grbl_pause'
WORKER_RESUME_REQUEST = 'grbl_resume'


class WorkerStoreAdapter:
    @classmethod
    def is_device_enabled(cls):
        return not not get_value(WORKER_IS_ENABLED_KEY)

    @classmethod
    def set_device_enabled(cls, enabled: bool):
        if enabled:
            return set_value(WORKER_IS_ENABLED_KEY, 'True')

        delete_value(WORKER_IS_ENABLED_KEY)

    @classmethod
    def is_device_paused(cls):
        return not not get_value(WORKER_IS_PAUSED_KEY)

    @classmethod
    def set_device_paused(cls, paused: bool):
        if paused:
            return set_value(WORKER_IS_PAUSED_KEY, 'True')

        delete_value(WORKER_IS_PAUSED_KEY)

    # IPC methods

    @classmethod
    def get_request(cls):
        """Get the asynchronous requests from client program.
        Take into account that the value is "popped" out the store.

        Possible requests:
        - pause
        - resume
        - stop
        """
        request = get_value(WORKER_REQUEST_KEY)
        delete_value(WORKER_REQUEST_KEY)

        return request

    @classmethod
    def request_pause(cls):
        set_value(WORKER_REQUEST_KEY, WORKER_PAUSE_REQUEST)

    @classmethod
    def request_resume(cls):
        set_value(WORKER_REQUEST_KEY, WORKER_RESUME_REQUEST)


class WorkerStatusManager:
    def __init__(self):
        self._paused = False

    def process_request(self) -> tuple[bool, bool]:
        """Checks if PAUSE or RESUME was requested, and updates the state.
        If status is not updated, the request is ignored.

        Returns: Tuple(paused: bool, resumed: bool)
        """
        request = WorkerStoreAdapter.get_request()

        if request == WORKER_PAUSE_REQUEST and not self._paused:
            WorkerStoreAdapter.set_device_paused(True)
            self._paused = True
            return True, False

        if request == WORKER_RESUME_REQUEST and self._paused:
            WorkerStoreAdapter.set_device_paused(False)
            self._paused = False
            return False, True

        return False, False

    def is_paused(self):
        return self._paused
