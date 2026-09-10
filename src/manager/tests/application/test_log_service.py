from unittest.mock import MagicMock

from manager.application.log_service import LogService


class TestLogService:
    @staticmethod
    def _make_service():
        storage = MagicMock()
        service = LogService(storage)
        return service, storage

    def test_classify_log_files(self):
        service, _ = self._make_service()
        expected = [{"file_name": "worker.log", "description": "Worker"}]
        service._manager.classify_log_files = MagicMock(return_value=expected)

        result = service.classify_log_files()

        assert result == expected

    def test_log_operations_delegate_to_manager(self):
        service, _ = self._make_service()
        service._manager.get_log_path = MagicMock(return_value="/tmp/app.log")
        service._manager.log_exists = MagicMock(return_value=True)
        service._manager.generate_log_csv = MagicMock(return_value="name,value\n")

        assert service.get_log_path("app.log") == "/tmp/app.log"
        assert service.log_exists("app.log") is True
        assert service.generate_log_csv("app.log") == "name,value\n"
        service._manager.get_log_path.assert_called_once_with("app.log")
        service._manager.log_exists.assert_called_once_with("app.log")
        service._manager.generate_log_csv.assert_called_once_with("app.log")
