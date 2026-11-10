from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.synchronization import SyncState


class SyncStateRepository(Protocol):
    async def create(self, sync_state: SyncState) -> bool: ...
    async def update(
        self,
        user_id: UUID,
        sync_state: SyncState,
        expected_version: int | None,
        expected_updated_at: datetime,
    ) -> bool: ...
    async def delete(self, user_id: UUID, sync_state_id: UUID) -> bool: ...
    async def get_sync_state(
        self, user_id: UUID, sync_state_id: UUID
    ) -> SyncState | None: ...
