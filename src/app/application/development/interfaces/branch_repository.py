from typing import Protocol
from uuid import UUID

from app.domain.development.entities.branch import Branch


class BranchRepository(Protocol):
    async def get_by_id(self, user_id: UUID, branch_id: UUID) -> Branch | None: ...

    async def get_by_repository(
        self, user_id: UUID, repository_id: UUID
    ) -> list[Branch]: ...

    async def get_by_name(
        self, user_id: UUID, repository_id: UUID, name: str, is_remote: bool
    ) -> Branch | None: ...

    async def create(self, user_id: UUID, branch: Branch) -> None: ...

    async def update(self, user_id: UUID, branch: Branch) -> bool: ...

    async def delete(self, user_id: UUID, branch_id: UUID) -> bool: ...
