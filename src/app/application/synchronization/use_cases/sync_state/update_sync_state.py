from datetime import UTC, datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.synchronization.dto.sync_state_data import SyncStateData
from app.application.synchronization.exceptions import (
    SyncStateNotFound,
    SyncStateUpdateConflict,
    SyncStateVersionConflict,
)
from app.application.synchronization.interfaces import (
    SyncStateRepository,
)
from app.domain.synchronization import InvalidSyncState, SyncState, SyncStatus


class UpdateSyncState:
    def __init__(self, sync_state_repository: SyncStateRepository) -> None:
        self._sync_state_repository = sync_state_repository

    async def execute(
        self,
        sync_state_id: UUID,
        identity: VerifiedIdentity,
        expected_version: int,
        server_version: int,
        status: SyncStatus,
        last_error: str | None,
    ) -> SyncStateData:
        existing_sync_state = await self._sync_state_repository.get_sync_state(
            user_id=identity.user_id, sync_state_id=sync_state_id
        )

        if existing_sync_state is None:
            raise SyncStateNotFound(str(sync_state_id))

        if existing_sync_state.local_version != expected_version:
            raise SyncStateVersionConflict(
                expected_version, existing_sync_state.local_version
            )
        try:
            now = datetime.now(UTC)
            sync_state = SyncState(
                sync_state_id=existing_sync_state.id,
                user_id=identity.user_id,
                client_device_id=existing_sync_state.client_device_id,
                entity_type=existing_sync_state.entity_type,
                entity_id=existing_sync_state.entity_id,
                updated_at=now,
                local_version=expected_version + 1,
                server_version=server_version,
                status=status,
                last_synced_at=(
                    now
                    if status is SyncStatus.SYNCED
                    else existing_sync_state.last_synced_at
                ),
                last_error=last_error,
            )
        except (InvalidSyncState, ValueError) as error:
            raise InvalidInput(str(error)) from error
        result = await self._sync_state_repository.update(
            user_id=identity.user_id,
            sync_state=sync_state,
            expected_version=expected_version,
            expected_updated_at=existing_sync_state.updated_at,
        )

        if not result:
            latest_sync_state = await self._sync_state_repository.get_sync_state(
                user_id=identity.user_id,
                sync_state_id=sync_state_id,
            )
            if latest_sync_state is None:
                raise SyncStateNotFound(str(sync_state_id))
            if latest_sync_state.local_version == expected_version:
                raise SyncStateUpdateConflict(str(sync_state_id))
            raise SyncStateVersionConflict(
                expected_version,
                latest_sync_state.local_version,
            )

        return SyncStateData.from_sync_state(sync_state)
