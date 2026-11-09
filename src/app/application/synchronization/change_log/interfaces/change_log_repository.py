from typing import Protocol
from uuid import UUID

from app.domain.synchronization import ChangeLog


class ChangeLogRepository(Protocol):
    async def create(self, change: ChangeLog) -> None: ...

    async def get_by_user(
        self, user_id: UUID, after_sequence: int, limit: int
    ) -> list[ChangeLog]: ...
