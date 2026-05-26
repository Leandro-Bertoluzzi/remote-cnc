"""Tests for FileManager."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from core.application.file_manager import FileManager
from core.domain.entities import File
from core.ports.file_repository import IFileRepository
from core.ports.file_storage import IFileStorage

GCODE_CONTENT = b"G1 X10 Y20\nG1 X30 Y40\nG1 X50 Y60"
EXPECTED_HASH = "987d1fbbfe0da6111b6214ab798984bd96f45554c2c896bce758152045120937"
BASE_PATH = "path/to/gcode_files/"


@pytest.fixture
def mock_storage() -> MagicMock:
    return MagicMock(spec=IFileStorage)


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock(spec=IFileRepository)


@pytest.fixture
def file_manager(mock_repo, mock_storage) -> FileManager:
    return FileManager(mock_repo, mock_storage)


# ---------------------------------------------------------------------------
# _compute_hash_from_file
# ---------------------------------------------------------------------------


def test_compute_hash_from_file(mocker, file_manager):
    mocked_open = mocker.mock_open(read_data=GCODE_CONTENT)
    mocker.patch("builtins.open", mocked_open)

    with open("/path/to/file", "rb") as f:
        result = file_manager._compute_hash_from_file(f)

    assert result == EXPECTED_HASH


# ---------------------------------------------------------------------------
# _compute_hash
# ---------------------------------------------------------------------------


def test_compute_hash(mocker, file_manager):
    mocked_open = mocker.mock_open(read_data=GCODE_CONTENT)
    mocker.patch("builtins.open", mocked_open)

    result = file_manager._compute_hash("path/to/file.gcode")
    assert result == EXPECTED_HASH


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------


def test_read_file(file_manager, mock_storage, mock_repo):
    mock_file = MagicMock(spec=File)
    mock_file.user_id = 1
    mock_file.file_name = "file.gcode"
    mock_repo.get_file_by_id.return_value = mock_file
    mock_storage.read_file.return_value = "G1 X10"

    result = file_manager.read_file(1)

    mock_repo.get_file_by_id.assert_called_once_with(1)
    mock_storage.read_file.assert_called_once_with(1, "file.gcode")
    assert result == "G1 X10"


# ---------------------------------------------------------------------------
# upload_file
# ---------------------------------------------------------------------------


def test_upload_file(mocker, file_manager, mock_storage, mock_repo):
    mocker.patch.object(FileManager, "_compute_hash_from_file", return_value="abc123")
    mock_created_file = MagicMock(spec=File)
    mock_storage.save_file.return_value = Path("path/1/file.gcode")
    mock_repo.create_file.return_value = mock_created_file

    result = file_manager.upload_file(1, "file.gcode", MagicMock())

    mock_repo.check_file_exists.assert_called_once_with(1, "file.gcode", "abc123")
    mock_storage.save_file.assert_called_once()
    mock_repo.create_file.assert_called_once_with(1, "file.gcode", "abc123")
    assert result is mock_created_file


def test_upload_file_rollback_on_db_error(mocker, file_manager, mock_storage, mock_repo):
    mocker.patch.object(FileManager, "_compute_hash_from_file", return_value="abc123")
    created_path = MagicMock(spec=Path)
    mock_storage.save_file.return_value = created_path
    mock_repo.create_file.side_effect = Exception("db error")

    with pytest.raises(Exception, match="db error"):
        file_manager.upload_file(1, "file.gcode", MagicMock())

    created_path.unlink.assert_called_once_with(missing_ok=True)


# ---------------------------------------------------------------------------
# create_file
# ---------------------------------------------------------------------------


def test_create_file(mocker, file_manager, mock_storage, mock_repo):
    mocker.patch.object(FileManager, "_compute_hash", return_value="def456")
    mock_created_file = MagicMock(spec=File)
    mock_storage.copy_file.return_value = Path("path/1/file.gcode")
    mock_repo.create_file.return_value = mock_created_file

    result = file_manager.create_file(1, "file.gcode", "/origin/file.gcode")

    mock_repo.check_file_exists.assert_called_once_with(1, "file.gcode", "def456")
    mock_storage.copy_file.assert_called_once_with(1, "/origin/file.gcode", "file.gcode")
    assert result is mock_created_file


def test_create_file_rollback_on_db_error(mocker, file_manager, mock_storage, mock_repo):
    mocker.patch.object(FileManager, "_compute_hash", return_value="def456")
    created_path = MagicMock(spec=Path)
    mock_storage.copy_file.return_value = created_path
    mock_repo.create_file.side_effect = Exception("db error")

    with pytest.raises(Exception, match="db error"):
        file_manager.create_file(1, "file.gcode", "/origin/file.gcode")

    created_path.unlink.assert_called_once_with(missing_ok=True)


# ---------------------------------------------------------------------------
# rename_file
# ---------------------------------------------------------------------------


def test_rename_file(file_manager, mock_storage, mock_repo):
    mock_file = MagicMock(spec=File)
    mock_file.id = 5
    mock_file.user_id = 1
    mock_file.file_name = "old.gcode"
    mock_storage.get_file_path.return_value = Path("path/1/old.gcode")
    mock_storage.rename_file.return_value = Path("path/1/new.gcode")
    mock_updated = MagicMock(spec=File)
    mock_repo.update_file.return_value = mock_updated

    result = file_manager.rename_file(1, mock_file, "new.gcode")

    mock_repo.check_file_exists.assert_called_once()
    mock_storage.rename_file.assert_called_once_with(1, "old.gcode", "new.gcode")
    mock_repo.update_file.assert_called_once_with(5, 1, "new.gcode")
    assert result is mock_updated


def test_rename_file_rollback_on_db_error(file_manager, mock_storage, mock_repo):
    mock_file = MagicMock(spec=File)
    mock_file.id = 5
    mock_file.user_id = 1
    mock_file.file_name = "old.gcode"
    original_path = Path("path/1/old.gcode")
    updated_path = MagicMock(spec=Path)
    mock_storage.get_file_path.return_value = original_path
    mock_storage.rename_file.return_value = updated_path
    mock_repo.update_file.side_effect = Exception("db error")

    with pytest.raises(Exception, match="db error"):
        file_manager.rename_file(1, mock_file, "new.gcode")

    updated_path.rename.assert_called_once_with(original_path)


# ---------------------------------------------------------------------------
# rename_file_by_id
# ---------------------------------------------------------------------------


def test_rename_file_by_id(mocker, file_manager, mock_storage, mock_repo):
    mock_file = MagicMock(spec=File)
    mock_file.id = 5
    mock_file.user_id = 1
    mock_file.file_name = "old.gcode"
    mock_repo.get_file_by_id.return_value = mock_file
    mock_rename = mocker.patch.object(FileManager, "rename_file", return_value=MagicMock())

    file_manager.rename_file_by_id(1, 5, "new.gcode")

    mock_repo.get_file_by_id.assert_called_once_with(5)
    mock_rename.assert_called_once_with(1, mock_file, "new.gcode")


# ---------------------------------------------------------------------------
# remove_file
# ---------------------------------------------------------------------------


def test_remove_file(file_manager, mock_storage, mock_repo):
    mock_file = MagicMock(spec=File)
    mock_file.id = 3
    mock_file.user_id = 1
    mock_file.file_name = "file.gcode"
    mock_storage.get_file_path.return_value = MagicMock(spec=Path, exists=lambda: False)

    file_manager.remove_file(mock_file)

    mock_storage.delete_file.assert_called_once_with(1, "file.gcode")
    mock_repo.remove_file.assert_called_once_with(3)


def test_remove_file_rollback_on_db_error(mocker, file_manager, mock_storage, mock_repo):
    mock_file = MagicMock(spec=File)
    mock_file.id = 3
    mock_file.user_id = 1
    mock_file.file_name = "file.gcode"
    mock_storage.get_file_path.return_value = MagicMock(spec=Path, exists=lambda: False)
    mock_repo.remove_file.side_effect = Exception("db error")
    mock_rollback = mocker.patch.object(FileManager, "_rollback_removed")

    with pytest.raises(Exception, match="db error"):
        file_manager.remove_file(mock_file)

    mock_rollback.assert_called_once()


# ---------------------------------------------------------------------------
# remove_file_by_id
# ---------------------------------------------------------------------------


def test_remove_file_by_id(mocker, file_manager, mock_repo):
    mock_file = MagicMock(spec=File)
    mock_repo.get_file_by_id.return_value = mock_file
    mock_remove = mocker.patch.object(FileManager, "remove_file")

    file_manager.remove_file_by_id(3)

    mock_repo.get_file_by_id.assert_called_once_with(3)
    mock_remove.assert_called_once_with(mock_file)
