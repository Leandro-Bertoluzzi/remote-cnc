from unittest.mock import MagicMock

from desktop.services.assetService import AssetService
from pytest_mock.plugin import MockerFixture


class TestAssetService:
    def test_get_assets(self, mocker: MockerFixture):
        session = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = session
        session_ctx.__exit__.return_value = None

        mocker.patch("desktop.services.assetService.get_db_session", return_value=session_ctx)

        file_repository = MagicMock()
        material_repository = MagicMock()
        tool_repository = MagicMock()

        get_file_repo = mocker.patch(
            "desktop.services.assetService.get_file_repository",
            return_value=file_repository,
        )
        get_material_repo = mocker.patch(
            "desktop.services.assetService.get_material_repository",
            return_value=material_repository,
        )
        get_tool_repo = mocker.patch(
            "desktop.services.assetService.get_tool_repository",
            return_value=tool_repository,
        )

        files = [MagicMock(), MagicMock()]
        materials = [MagicMock()]
        tools = [MagicMock(), MagicMock(), MagicMock()]
        file_repository.get_all_files_from_user.return_value = files
        material_repository.get_all_materials.return_value = materials
        tool_repository.get_all_tools.return_value = tools

        result = AssetService.get_assets(user_id=5)

        assert result == (files, materials, tools)
        get_file_repo.assert_called_once_with(session)
        get_material_repo.assert_called_once_with(session)
        get_tool_repo.assert_called_once_with(session)
        file_repository.get_all_files_from_user.assert_called_once_with(5)
        material_repository.get_all_materials.assert_called_once_with()
        tool_repository.get_all_tools.assert_called_once_with()
