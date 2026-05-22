from unittest.mock import MagicMock

from desktop.services.materialService import MaterialService
from pytest_mock.plugin import MockerFixture


class TestMaterialService:
    @staticmethod
    def _mock_db_and_repo(mocker: MockerFixture):
        session = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = session
        session_ctx.__exit__.return_value = None

        mocker.patch("desktop.services.materialService.get_db_session", return_value=session_ctx)
        repository = MagicMock()
        get_repo = mocker.patch(
            "desktop.services.materialService.get_material_repository",
            return_value=repository,
        )
        return session, repository, get_repo

    def test_get_all_materials(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)
        expected = [MagicMock(), MagicMock()]
        repository.get_all_materials.return_value = expected

        result = MaterialService.get_all_materials()

        assert result == expected
        get_repo.assert_called_once_with(session)
        repository.get_all_materials.assert_called_once_with()

    def test_create_material(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        result = MaterialService.create_material("MDF", "desc")

        get_repo.assert_called_once_with(session)
        repository.create_material.assert_called_once_with("MDF", "desc")
        assert result is None

    def test_remove_material(self, mocker: MockerFixture):
        session, repository, get_repo = self._mock_db_and_repo(mocker)

        MaterialService.remove_material(material_id=2)

        get_repo.assert_called_once_with(session)
        repository.remove_material.assert_called_once_with(2)
