from io import StringIO
from pathlib import Path

from core.application.log_manager import LogManager


class FakeLogStorage:
    def __init__(self, files: dict[str, str]):
        self._files = files

    def get_log_path(self, file_name: str) -> Path:
        return Path("/app/logs") / file_name

    def log_exists(self, filename: str) -> bool:
        return filename in self._files

    def get_all_log_paths(self) -> list[str]:
        return list(self._files.keys())

    def open_for_reading(self, filename: str):
        return StringIO(self._files[filename])


class TestLogsManager:
    def test_get_log_path(self):
        manager = LogManager(FakeLogStorage({}))
        assert manager.get_log_path("worker.log") == Path("/app/logs/worker.log")

    def test_log_exists(self):
        manager = LogManager(FakeLogStorage({"worker.log": ""}))
        assert manager.log_exists("worker.log") is True
        assert manager.log_exists("missing.log") is False

    def test_classify_log_files(self):
        manager = LogManager(
            FakeLogStorage(
                {
                    "task_file_20240228_194555.log": "",
                    "worker.log": "",
                    "controller.log": "",
                    "notes.txt": "",
                    "task_invalid.log": "",
                }
            )
        )

        result = manager.classify_log_files()
        by_name = {entry["file_name"]: entry["description"] for entry in result}

        assert "notes.txt" not in by_name
        assert "task_invalid.log" not in by_name
        assert by_name["worker.log"] == "Registros del worker"
        assert by_name["controller.log"] == "Registros del controlador grbl"
        assert "Ejecución del archivo <<file>> el día 28/02/2024 a las 19:45:55" == by_name[
            "task_file_20240228_194555.log"
        ]

    def test_interpret_file(self):
        manager = LogManager(
            FakeLogStorage(
                {
                    "task_file_20240228_194555.log": (
                        "[28/02/2024 19:45:55] INFO: Started USB connection at port COM5\n"
                        "[28/02/2024 19:45:55] WARNING: Handling homing cycle at startup...\n"
                        "[28/02/2024 19:45:55] INFO: [Sent] command: $X\n"
                        "invalid line, just ignore\n"
                    )
                }
            )
        )

        assert list(manager.interpret_file("task_file_20240228_194555.log")) == [
            ("28/02/2024 19:45:55", "INFO", None, "Started USB connection at port COM5"),
            ("28/02/2024 19:45:55", "WARNING", None, "Handling homing cycle at startup..."),
            ("28/02/2024 19:45:55", "INFO", "Sent", "command: $X"),
        ]

    def test_interpret_file_non_existing(self):
        manager = LogManager(FakeLogStorage({}))

        result = manager.interpret_file("missing.log")

        assert list(result) == []

    def test_generate_log_csv(self):
        manager = LogManager(
            FakeLogStorage(
                {
                    "worker.log": (
                        "[28/02/2024 19:45:55] INFO: [Sent] command: $X\n"
                        "[28/02/2024 19:45:55] WARNING: Handling homing cycle at startup...\n"
                        "[28/02/2024 19:47:59] INFO: [Parsed] Message type: GrblResultOk\n"
                    )
                }
            )
        )

        csv_content = manager.generate_log_csv("worker.log")

        assert "Fecha y hora,Nivel,Tipo,Mensaje" in csv_content
        assert "28/02/2024 19:45:55,INFO,Sent,command: $X" in csv_content
        assert "28/02/2024 19:45:55,WARNING,,Handling homing cycle at startup..." in csv_content
        assert "28/02/2024 19:47:59,INFO,Parsed,Message type: GrblResultOk" in csv_content
