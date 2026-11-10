from datetime import UTC, datetime
from uuid import uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceGroupData
from app.application.infrastructure.interfaces import DeviceGroupRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import DeviceGroup, DeviceGroupName, InvalidDeviceGroup
from app.domain.synchronization import ChangeOperation


class CreateDeviceGroup:
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
    async def execute(
        self,
        identity: VerifiedIdentity,
        name: str,
        description: str | None,
    ) -> DeviceGroupData:
        try:
            device_group_name = DeviceGroupName(name)
            now = datetime.now(UTC)
            device_group = DeviceGroup(
                entity_id=uuid4(),
                user_id=identity.user_id,
                description=description,
                name=device_group_name,
                created_at=now,
                updated_at=now,
            )
        except InvalidDeviceGroup as error:
            raise InvalidInput(str(error)) from error

        await self._device_group_repository.create(device_group=device_group)
        await self._recorder.execute(
            identity,
            EntityType.DEVICE_GROUP,
            device_group.id,
            ChangeOperation.INSERT,
            device_group.version,
            {"name": device_group.name, "description": device_group.description},
        )

        return DeviceGroupData.from_device_group(device_group=device_group)
