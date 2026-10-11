from __future__ import annotations

from pathlib import Path


class FakeGatewayClient:
    def __init__(self) -> None:
        self.state: str | None = "idle"
        self.last_status: dict | None = None
        self.active_session: dict | None = None
        self.commands: list[tuple[str, str]] = []
        self.jogs: list[tuple[str, dict]] = []
        self.realtime_actions: list[tuple[str, str]] = []
        self._next_session_id = 1

    def acquire_session(self, user_id: int, client_type: str, ttl: int = 300) -> str | None:
        if self.active_session is not None:
            return None
        session_id = f"test-session-{self._next_session_id}"
        self._next_session_id += 1
        self.active_session = {
            "session_id": session_id,
            "user_id": user_id,
            "client_type": client_type,
            "created_at": 1_800_000_000.0,
        }
        return session_id

    def renew_session(self, session_id: str, ttl: int = 300) -> bool:
        return self.active_session is not None and self.active_session["session_id"] == session_id

    def release_session(self, session_id: str) -> bool:
        if self.active_session is None or self.active_session["session_id"] != session_id:
            return False
        self.active_session = None
        return True

    def get_active_session(self) -> dict | None:
        return self.active_session

    def send_command(self, session_id: str, command: str) -> None:
        self.commands.append((session_id, command))

    def send_jog(
        self,
        session_id: str,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        feedrate: float = 0,
        *,
        units: str | None = None,
        distance_mode: str | None = None,
        machine_coordinates: bool = False,
    ) -> None:
        self.jogs.append(
            (
                session_id,
                {
                    "x": x,
                    "y": y,
                    "z": z,
                    "feedrate": feedrate,
                    "units": units,
                    "distance_mode": distance_mode,
                    "machine_coordinates": machine_coordinates,
                },
            )
        )

    def send_realtime(self, session_id: str, action: str) -> None:
        self.realtime_actions.append((session_id, action))

    def send_query(self, session_id: str, query_type: str) -> None:
        self.commands.append((session_id, query_type))

    def request_file_execution(
        self,
        session_id: str,
        file_path: str,
        task_id: int | None = None,
        shared_logger_name: str | None = None,
    ) -> None:
        self.commands.append((session_id, file_path))

    def request_file_stop(self, session_id: str) -> None:
        self.commands.append((session_id, "stop_file"))

    def request_disconnect(self, session_id: str) -> None:
        self.commands.append((session_id, "disconnect"))

    def get_gateway_state(self) -> str | None:
        return self.state

    def get_last_status(self) -> dict | None:
        return self.last_status

    def is_gateway_running(self) -> bool:
        return self.state is not None

    def flush_queues(self) -> int:
        count = len(self.commands) + len(self.jogs) + len(self.realtime_actions)
        self.commands.clear()
        self.jogs.clear()
        self.realtime_actions.clear()
        return count

    def subscribe_events(self):
        raise NotImplementedError("PubSub is not used by API route unit tests")

    def subscribe_channels(self, *channels: str):
        raise NotImplementedError("PubSub is not used by API route unit tests")


class FakeWorkerClient:
    def __init__(self) -> None:
        self.online = True
        self.running = False
        self.dispatch_error: Exception | None = None
        self.dispatched_tasks: list[int] = []
        self.dispatched_thumbnails: list[int] = []
        self.dispatched_reports: list[int] = []

    def is_on(self) -> bool:
        return self.online

    def is_running(self) -> bool:
        return self.running

    def get_status(self) -> dict:
        return {
            "connected": self.online,
            "running": self.running,
            "stats": None,
            "registered_tasks": None,
            "active_tasks": None,
        }

    def send_task(self, db_task_id: int) -> str:
        if self.dispatch_error:
            raise self.dispatch_error
        self.dispatched_tasks.append(db_task_id)
        return f"worker-task-{len(self.dispatched_tasks)}"

    def create_thumbnail(self, file_id: int) -> str:
        if self.dispatch_error:
            raise self.dispatch_error
        self.dispatched_thumbnails.append(file_id)
        return f"thumbnail-{len(self.dispatched_thumbnails)}"

    def generate_file_report(self, file_id: int) -> str:
        if self.dispatch_error:
            raise self.dispatch_error
        self.dispatched_reports.append(file_id)
        return f"report-{len(self.dispatched_reports)}"


class FakeLogStorage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def get_log_path(self, file_name: str) -> Path:
        return self.root / file_name

    def log_exists(self, file_name: str) -> bool:
        return self.get_log_path(file_name).is_file()

    def get_all_log_paths(self) -> list[str]:
        return [path.name for path in self.root.iterdir() if path.is_file()]

    def open_for_reading(self, filename: str):
        return self.get_log_path(filename).open("r", encoding="utf-8")

    def write_log(self, file_name: str, contents: str) -> Path:
        path = self.get_log_path(file_name)
        path.write_text(contents, encoding="utf-8")
        return path
