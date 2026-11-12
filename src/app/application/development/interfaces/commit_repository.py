from typing import Protocol
from uuid import UUID

from app.domain.development.entities.commit import Commit


class CommitRepository(Protocol):
    async def get_by_id(self, user_id: UUID, commit_id: UUID) -> Commit | None: ...

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[Commit]: ...

    async def get_by_hash(
        self, user_id: UUID, repository_id: UUID, commit_hash: str
    ) -> Commit | None: ...

    async def create(self, user_id: UUID, commit: Commit) -> None: ...
