"""Tests for the G-code file processing handlers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from core.domain.entities import File
from core.ports.file_repository import IFileRepository
from core.ports.file_storage import IFileStorage
from worker.ports.renderer import IRenderer
from worker.tasks.handlers.files_handler import (
    create_thumbnail_handler,
    generate_file_report_handler,
)


def _make_file(file_id: int = 1) -> MagicMock:
    f = MagicMock(spec=File)
    f.id = file_id
    f.user_id = 2
    f.file_name = "part.gcode"
    return f


# ---------------------------------------------------------------------------
# create_thumbnail_handler
# ---------------------------------------------------------------------------


def test_create_thumbnail_success():
    """Thumbnail is generated and renderer is called with correct paths."""
    repo = MagicMock(spec=IFileRepository)
    storage = MagicMock(spec=IFileStorage)
    renderer = MagicMock(spec=IRenderer)
    file = _make_file(file_id=7)
    repo.get_file_by_id.return_value = file
    storage.get_file_path.return_value = Path("/files/2/part.gcode")

    create_thumbnail_handler(
        file_id=7,
        repo=repo,
        storage=storage,
        images_folder="/images",
        renderer=renderer,
    )

    repo.get_file_by_id.assert_called_once_with(7)
    storage.get_file_path.assert_called_once_with(2, "part.gcode")
    renderer.run.assert_called_once_with(
        str(Path("/files/2/part.gcode")), "/images/img7.png", moves=False
    )


def test_create_thumbnail_file_not_found():
    """Raises exception when file is not in the DB."""
    repo = MagicMock(spec=IFileRepository)
    repo.get_file_by_id.return_value = None
    storage = MagicMock(spec=IFileStorage)
    renderer = MagicMock(spec=IRenderer)

    with pytest.raises(Exception, match="No se encontró el archivo"):
        create_thumbnail_handler(
            file_id=99, repo=repo, storage=storage, images_folder="/images", renderer=renderer
        )


# ---------------------------------------------------------------------------
# generate_file_report_handler
# ---------------------------------------------------------------------------


def test_generate_file_report_success():
    """Report is analysed and saved to the repository."""
    repo = MagicMock(spec=IFileRepository)
    storage = MagicMock(spec=IFileStorage)
    file = _make_file(file_id=3)
    repo.get_file_by_id.return_value = file
    storage.get_file_path.return_value = Path("/files/2/part.gcode")

    fake_report = {"lines": 100, "gcodes": ["G0", "G1"]}

    with patch("worker.tasks.handlers.files_handler.GcodeAnalyser") as mock_analyser_cls:
        mock_analyser_cls.return_value.analyse.return_value = fake_report
        generate_file_report_handler(
            file_id=3,
            repo=repo,
            storage=storage,
            valid_gcodes=["G0", "G1"],
            valid_mcodes=["M3"],
        )

    repo.get_file_by_id.assert_called_once_with(3)
    storage.get_file_path.assert_called_once_with(2, "part.gcode")
    mock_analyser_cls.assert_called_once_with(Path("/files/2/part.gcode"), ["G0", "G1"], ["M3"])
    mock_analyser_cls.return_value.analyse.assert_called_once()
    repo.save_file_report.assert_called_once_with(3, fake_report)


def test_generate_file_report_file_not_found():
    """Raises exception when file is not in the DB."""
    repo = MagicMock(spec=IFileRepository)
    repo.get_file_by_id.return_value = None
    storage = MagicMock(spec=IFileStorage)

    with pytest.raises(Exception, match="No se encontró el archivo"):
        generate_file_report_handler(
            file_id=99, repo=repo, storage=storage, valid_gcodes=[], valid_mcodes=[]
        )
