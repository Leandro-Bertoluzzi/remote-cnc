"""Port for file persistence operations."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.domain.entities import File
from core.domain.types import FileReport


@runtime_checkable
class IFileRepository(Protocol):
    def check_file_exists(self, user_id: int, file_name: str, file_hash: str) -> None: ...

    def create_file(self, user_id: int, file_name: str, file_hash: str) -> File: ...

    def get_all_files_from_user(self, user_id: int) -> list[File]: ...

    def get_all_files(self) -> list[File]: ...

    def get_file_by_id(self, id: int) -> File: ...

    def update_file(
        self,
        id: int,
        user_id: int,
        file_name: str,
        file_hash: str | None = None,
    ) -> File: ...

    def save_file_report(self, id: int, report: FileReport) -> None: ...

    def remove_file(self, id: int) -> None: ...
