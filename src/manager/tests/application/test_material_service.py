from unittest.mock import MagicMock

from manager.application.material_service import MaterialService


class TestMaterialService:
    @staticmethod
    def _make_service_and_repo():
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None
        repository = MagicMock()
        service = MaterialService(
            session_factory=session_factory,
            material_repo_factory=MagicMock(return_value=repository),
        )
        return service, repository

    def test_get_all_materials(self):
        service, repository = self._make_service_and_repo()
        expected = [MagicMock(), MagicMock()]
        repository.get_all_materials.return_value = expected

        result = service.get_all_materials()

        assert result == expected
        repository.get_all_materials.assert_called_once_with()

    def test_create_material(self):
        service, repository = self._make_service_and_repo()
        expected = MagicMock()
        repository.create_material.return_value = expected

        result = service.create_material("MDF", "desc")

        repository.create_material.assert_called_once_with("MDF", "desc")
        assert result == expected

    def test_update_material(self):
        service, repository = self._make_service_and_repo()
        expected = MagicMock()
        repository.update_material.return_value = expected

        result = service.update_material(3, "MDF Updated", "new desc")

        repository.update_material.assert_called_once_with(3, "MDF Updated", "new desc")
        assert result == expected

    def test_remove_material(self):
        service, repository = self._make_service_and_repo()

        service.remove_material(material_id=2)

        repository.remove_material.assert_called_once_with(2)
