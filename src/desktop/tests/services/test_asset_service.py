from unittest.mock import MagicMock

from desktop.services.assetService import AssetService
from pytest_mock.plugin import MockerFixture


class TestAssetService:
    def test_get_assets(self, mocker: MockerFixture):
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        file_repository = MagicMock()
        material_repository = MagicMock()
        tool_repository = MagicMock()

        files = [MagicMock(), MagicMock()]
        materials = [MagicMock()]
        tools = [MagicMock(), MagicMock(), MagicMock()]
        file_repository.get_all_files_from_user.return_value = files
        material_repository.get_all_materials.return_value = materials
        tool_repository.get_all_tools.return_value = tools

        mocker.patch(
            "desktop.services.assetService.get_file_repository", return_value=file_repository
        )
        mocker.patch(
            "desktop.services.assetService.get_material_repository",
            return_value=material_repository,
        )
        mocker.patch(
            "desktop.services.assetService.get_tool_repository", return_value=tool_repository
        )

        service = AssetService(session_factory=session_factory)
        result = service.get_assets(user_id=5)

        assert result == (files, materials, tools)
        file_repository.get_all_files_from_user.assert_called_once_with(5)
        material_repository.get_all_materials.assert_called_once_with()
        tool_repository.get_all_tools.assert_called_once_with()
