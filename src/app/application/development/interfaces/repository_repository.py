from typing import Protocol
from uuid import UUID

from app.domain.development.entities.repository import Repository


class RepositoryRepository(Protocol):
    async def get_by_id(self, user_id: UUID, repository_id: UUID) -> Repository | None: ...

    async def get_by_user(self, user_id: UUID) -> list[Repository]: ...

    async def get_by_project(self, user_id: UUID, project_id: UUID) -> list[Repository]: ...

    async def create(self, repository: Repository) -> None: ...

    async def update(
        self, user_id: UUID, repository: Repository, expected_version: int
    ) -> bool: ...

    async def delete(
        self, user_id: UUID, repository_id: UUID, expected_version: int
    ) -> bool: ...
