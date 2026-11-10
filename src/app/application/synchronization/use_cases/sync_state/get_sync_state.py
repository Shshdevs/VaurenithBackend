from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.synchronization.dto.sync_state_data import SyncStateData
from app.application.synchronization.exceptions import SyncStateNotFound
from app.application.synchronization.interfaces import (
    SyncStateRepository,
)


class GetSyncState:
    def __init__(self, sync_state_repository: SyncStateRepository) -> None:
        self._sync_state_repository = sync_state_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        sync_state_id: UUID,
    ) -> SyncStateData:
        result = await self._sync_state_repository.get_sync_state(
            user_id=identity.user_id,
            sync_state_id=sync_state_id,
        )
        if result is None:
            raise SyncStateNotFound(str(sync_state_id))

        return SyncStateData.from_sync_state(result)
