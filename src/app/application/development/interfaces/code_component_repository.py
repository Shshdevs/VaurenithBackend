from typing import Protocol
from uuid import UUID

from app.domain.development.entities.code_component import CodeComponent


class CodeComponentRepository(Protocol):
    async def get_by_id(
        self, user_id: UUID, component_id: UUID
    ) -> CodeComponent | None: ...

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[CodeComponent]: ...

    async def create(self, user_id: UUID, component: CodeComponent) -> None: ...

    async def update(
        self, user_id: UUID, component: CodeComponent, expected_version: int
    ) -> bool: ...

    async def delete(
        self, user_id: UUID, component_id: UUID, expected_version: int
    ) -> bool: ...
