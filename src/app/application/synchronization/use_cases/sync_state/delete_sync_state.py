from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.synchronization.exceptions import SyncStateNotFound
from app.application.synchronization.interfaces import (
    SyncStateRepository,
)


class DeleteSyncState:
    def __init__(self, sync_state_repository: SyncStateRepository) -> None:
        self._sync_state_repository = sync_state_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        sync_state_id: UUID,
    ) -> None:
        existing = await self._sync_state_repository.get_sync_state(
            user_id=identity.user_id, sync_state_id=sync_state_id
        )
        if existing is None:
            raise SyncStateNotFound(str(sync_state_id))
        result = await self._sync_state_repository.delete(
            user_id=identity.user_id, sync_state_id=sync_state_id
        )

        if not result:
            raise SyncStateNotFound(str(sync_state_id))
