from unittest.mock import MagicMock

from desktop.services.materialService import MaterialService
from pytest_mock.plugin import MockerFixture


class TestMaterialService:
    @staticmethod
    def _make_service_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None
        repository = MagicMock()
        mocker.patch(
            "desktop.services.materialService.get_material_repository",
            return_value=repository,
        )
        service = MaterialService(session_factory=session_factory)
        return service, session, repository

    def test_get_all_materials(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)
        expected = [MagicMock(), MagicMock()]
        repository.get_all_materials.return_value = expected

        result = service.get_all_materials()

        assert result == expected
        repository.get_all_materials.assert_called_once_with()

    def test_create_material(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)

        result = service.create_material("MDF", "desc")

        repository.create_material.assert_called_once_with("MDF", "desc")
        assert result is None

    def test_remove_material(self, mocker: MockerFixture):
        service, session, repository = self._make_service_and_repo(mocker)

        service.remove_material(material_id=2)

        repository.remove_material.assert_called_once_with(2)
