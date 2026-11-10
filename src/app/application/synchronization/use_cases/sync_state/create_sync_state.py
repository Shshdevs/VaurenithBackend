from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.synchronization.dto.sync_state_data import SyncStateData
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


class CreateSyncState:
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
        await self._recorder.execute(
            identity,
            EntityType.SYNC_STATE,
            sync_state.id,
            ChangeOperation.INSERT,
            sync_state.version,
            {
                "client_device_id": str(sync_state.client_device_id),
                "entity_type": (
                    sync_state.entity_type.value if sync_state.entity_type else None
                ),
                "entity_id": (str(sync_state.entity_id) if sync_state.entity_id else None),
                "local_version": sync_state.local_version,
                "server_version": sync_state.server_version,
                "status": sync_state.status.value,
            },
        )
        return SyncStateData.from_sync_state(sync_state)
