from datetime import UTC, datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.synchronization.dto.sync_state_data import SyncStateData
from app.application.synchronization.exceptions import (
    SyncStateNotFound,
    SyncStateUpdateConflict,
)
from app.application.synchronization.interfaces import (
    ChangeRecorder,
    SyncStateRepository,
)
from app.domain.common import EntityType
from app.domain.synchronization import (
    ChangeOperation,
    InvalidSyncState,
    SyncState,
    SyncStatus,
)


class UpdateSyncStatus:
    def __init__(
        self,
        sync_state_repository: SyncStateRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._sync_state_repository = sync_state_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        sync_state_id: UUID,
        identity: VerifiedIdentity,
        status: SyncStatus,
    ) -> SyncStateData:
        existing_sync_state = await self._sync_state_repository.get_sync_state(
            user_id=identity.user_id,
            sync_state_id=sync_state_id,
        )

        if existing_sync_state is None:
            raise SyncStateNotFound(str(sync_state_id))

        try:
            now = datetime.now(UTC)
            sync_state = SyncState(
                sync_state_id=existing_sync_state.id,
                user_id=identity.user_id,
                client_device_id=existing_sync_state.client_device_id,
                entity_type=existing_sync_state.entity_type,
                entity_id=existing_sync_state.entity_id,
                updated_at=now,
                local_version=existing_sync_state.local_version,
                server_version=existing_sync_state.server_version,
                status=status,
                last_synced_at=(
                    now
                    if status is SyncStatus.SYNCED
                    else existing_sync_state.last_synced_at
                ),
                last_error=existing_sync_state.last_error,
                version=existing_sync_state.version + 1,
            )
        except (InvalidSyncState, ValueError) as error:
            raise InvalidInput(str(error)) from error
        result = await self._sync_state_repository.update(
            user_id=identity.user_id,
            sync_state=sync_state,
            expected_version=existing_sync_state.local_version,
            expected_updated_at=existing_sync_state.updated_at,
        )

        if not result:
            latest_sync_state = await self._sync_state_repository.get_sync_state(
                user_id=identity.user_id,
                sync_state_id=sync_state_id,
            )
            if latest_sync_state is None:
                raise SyncStateNotFound(str(sync_state_id))
            raise SyncStateUpdateConflict(str(sync_state_id))

        await self._recorder.execute(
            identity,
            EntityType.SYNC_STATE,
            sync_state.id,
            ChangeOperation.UPDATE,
            sync_state.version,
            {"status": sync_state.status.value},
        )

        return SyncStateData.from_sync_state(sync_state)
