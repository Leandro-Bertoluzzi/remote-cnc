"""Port for material persistence operations."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.domain.entities import Material


@runtime_checkable
class IMaterialRepository(Protocol):
    def create_material(self, name: str, description: str) -> Material: ...

    def get_material_by_id(self, id: int) -> Material: ...

    def get_all_materials(self) -> list[Material]: ...

    def update_material(self, id: int, name: str, description: str) -> Material: ...

    def remove_material(self, id: int) -> None: ...
