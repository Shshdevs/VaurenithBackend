from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.synchronization.exceptions import SyncStateNotFound
from app.application.synchronization.interfaces import (
    ChangeRecorder,
    SyncStateRepository,
)
from app.domain.common import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteSyncState:
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
        await self._recorder.execute(
            identity,
            EntityType.SYNC_STATE,
            sync_state_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
