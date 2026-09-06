from unittest.mock import MagicMock

from manager.application.asset_service import AssetService


class TestAssetService:
    @staticmethod
    def _make_service_and_repos():
        session = MagicMock()
        session_factory = MagicMock()
        session_factory.return_value.__enter__.return_value = session
        session_factory.return_value.__exit__.return_value = None

        file_repo = MagicMock()
        material_repo = MagicMock()
        tool_repo = MagicMock()

        service = AssetService(
            session_factory=session_factory,
            file_repo_factory=MagicMock(return_value=file_repo),
            material_repo_factory=MagicMock(return_value=material_repo),
            tool_repo_factory=MagicMock(return_value=tool_repo),
        )
        return service, file_repo, material_repo, tool_repo

    def test_get_assets(self):
        service, file_repo, material_repo, tool_repo = self._make_service_and_repos()

        files = [MagicMock(), MagicMock()]
        materials = [MagicMock()]
        tools = [MagicMock(), MagicMock(), MagicMock()]
        file_repo.get_all_files_from_user.return_value = files
        material_repo.get_all_materials.return_value = materials
        tool_repo.get_all_tools.return_value = tools

        result = service.get_assets(user_id=5)

        assert result == (files, materials, tools)
        file_repo.get_all_files_from_user.assert_called_once_with(5)
        material_repo.get_all_materials.assert_called_once_with()
        tool_repo.get_all_tools.assert_called_once_with()
