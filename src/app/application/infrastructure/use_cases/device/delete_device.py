from datetime import UTC, datetime
from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.infrastructure.interfaces import DeviceRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteDevice:
    def __init__(
        self,
        device_repository: DeviceRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._device_repository = device_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, identity: VerifiedIdentity, device_id: UUID) -> None:
        existing = await self._device_repository.get_by_id(identity, device_id)
        if existing is None:
            raise DeviceNotFound(str(device_id))
        deleted = await self._device_repository.delete(
            identity, device_id, datetime.now(UTC)
        )
        if not deleted:
            raise DeviceNotFound(str(device_id))
        await self._recorder.execute(
            identity,
            EntityType.DEVICE,
            device_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
