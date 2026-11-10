from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.synchronization.dto.sync_state_data import SyncStateData
from app.application.synchronization.interfaces import (
    SyncStateRepository,
)
from app.domain.common import EntityType
from app.domain.synchronization import InvalidSyncState, SyncState, SyncStatus


class CreateSyncState:
    def __init__(self, sync_state_repository: SyncStateRepository) -> None:
        self._sync_state_repository = sync_state_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        client_device_id: UUID,
        entity_type: EntityType | None,
        entity_id: UUID | None,
        local_version: int | None,
        server_version: int | None,
        status: SyncStatus,
    ) -> SyncStateData:
        try:
            now = datetime.now(UTC)
            sync_state = SyncState(
                sync_state_id=uuid4(),
                user_id=identity.user_id,
                client_device_id=client_device_id,
                entity_type=entity_type,
                entity_id=entity_id,
                updated_at=now,
                local_version=local_version,
                server_version=server_version,
                status=status,
                last_synced_at=now if status is SyncStatus.SYNCED else None,
                last_error=None,
            )
        except InvalidSyncState as error:
            raise InvalidInput(str(error)) from error

        created = await self._sync_state_repository.create(sync_state=sync_state)
        if not created:
            raise InvalidInput("Client device does not belong to the authenticated user")
        return SyncStateData.from_sync_state(sync_state)
