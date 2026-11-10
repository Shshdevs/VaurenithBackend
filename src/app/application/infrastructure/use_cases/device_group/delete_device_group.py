from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceGroupNotFound
from app.application.infrastructure.interfaces import DeviceGroupRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteDeviceGroup:
    def __init__(
        self,
        device_group_repository: DeviceGroupRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._device_group_repository = device_group_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, identity: VerifiedIdentity, device_group_id: UUID) -> None:
        existing = await self._device_group_repository.get_by_id(identity, device_group_id)
        if existing is None:
            raise DeviceGroupNotFound(str(device_group_id))
        result = await self._device_group_repository.delete(
            identity=identity, device_group_id=device_group_id
        )

        if not result:
            raise DeviceGroupNotFound(str(device_group_id))
        await self._recorder.execute(
            identity,
            EntityType.DEVICE_GROUP,
            device_group_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
